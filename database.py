import sqlite3
import time
import csv

DB_PATH = "fleet_engine.db"

# ── INIT ──────────────────────────────────────────────────────────────

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c    = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS assignments (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            tick        INTEGER,
            timestamp   REAL,
            order_id    INTEGER,
            agent_id    INTEGER,
            distance    REAL,
            priority    INTEGER,
            deadline    REAL,
            score       REAL,
            event_type  TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS tick_snapshots (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            tick           INTEGER,
            timestamp      REAL,
            total_orders   INTEGER,
            delivered      INTEGER,
            reassigned     INTEGER,
            failed         INTEGER,
            on_time_rate   REAL,
            avg_distance   REAL,
            agents_busy    INTEGER,
            cost_saved_inr INTEGER
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            tick       INTEGER,
            timestamp  REAL,
            event_type TEXT,
            order_id   INTEGER,
            agent_id   INTEGER,
            message    TEXT
        )
    """)

    conn.commit()
    conn.close()
    print(f"[DB] Initialised → {DB_PATH}")

# ── WRITERS ───────────────────────────────────────────────────────────

def log_assignment(tick, order_id, agent_id, distance,
                   priority, deadline, score, event_type="ASSIGNED"):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        INSERT INTO assignments
        (tick, timestamp, order_id, agent_id, distance, priority, deadline, score, event_type)
        VALUES (?,?,?,?,?,?,?,?,?)
    """, (tick, time.time(), order_id, agent_id,
          distance, priority, deadline, score, event_type))
    conn.commit()
    conn.close()

def log_tick_snapshot(tick, total_orders, delivered, reassigned,
                      failed, on_time_rate, avg_distance,
                      agents_busy, cost_saved_inr):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        INSERT INTO tick_snapshots
        (tick, timestamp, total_orders, delivered, reassigned, failed,
         on_time_rate, avg_distance, agents_busy, cost_saved_inr)
        VALUES (?,?,?,?,?,?,?,?,?,?)
    """, (tick, time.time(), total_orders, delivered, reassigned,
          failed, on_time_rate, avg_distance, agents_busy, cost_saved_inr))
    conn.commit()
    conn.close()

def log_event(tick, event_type, order_id, agent_id, message):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        INSERT INTO events (tick, timestamp, event_type, order_id, agent_id, message)
        VALUES (?,?,?,?,?,?)
    """, (tick, time.time(), event_type, order_id, agent_id, message))
    conn.commit()
    conn.close()

# ── READERS ───────────────────────────────────────────────────────────

def get_tick_history(last_n=100):
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("""
        SELECT tick, on_time_rate, avg_distance, delivered,
               reassigned, agents_busy, cost_saved_inr
        FROM tick_snapshots
        ORDER BY tick DESC LIMIT ?
    """, (last_n,)).fetchall()
    conn.close()
    return list(reversed(rows))

def get_recent_events(last_n=50):
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("""
        SELECT tick, event_type, order_id, agent_id, message
        FROM events ORDER BY id DESC LIMIT ?
    """, (last_n,)).fetchall()
    conn.close()
    return rows

def get_full_stats():
    conn = sqlite3.connect(DB_PATH)
    stats = {}

    stats["total_assignments"] = conn.execute(
        "SELECT COUNT(*) FROM assignments WHERE event_type='ASSIGNED'"
    ).fetchone()[0]

    stats["total_reassignments"] = conn.execute(
        "SELECT COUNT(*) FROM assignments WHERE event_type='REASSIGNED'"
    ).fetchone()[0]

    stats["total_deliveries"] = conn.execute(
        "SELECT COUNT(*) FROM events WHERE event_type='DELIVERED'"
    ).fetchone()[0]

    stats["avg_score"] = conn.execute(
        "SELECT AVG(score) FROM assignments"
    ).fetchone()[0] or 0

    stats["avg_distance"] = conn.execute(
        "SELECT AVG(distance) FROM assignments"
    ).fetchone()[0] or 0

    stats["total_ticks"] = conn.execute(
        "SELECT COUNT(*) FROM tick_snapshots"
    ).fetchone()[0]

    conn.close()
    stats["avg_score"]    = round(stats["avg_score"], 4)
    stats["avg_distance"] = round(stats["avg_distance"], 2)
    return stats

def export_to_csv():
    conn = sqlite3.connect(DB_PATH)

    with open("assignments_export.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["tick", "timestamp", "order_id", "agent_id",
                         "distance", "priority", "deadline", "score", "event_type"])
        for row in conn.execute("SELECT * FROM assignments ORDER BY tick"):
            writer.writerow(row[1:])

    with open("tick_history_export.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["tick", "timestamp", "total_orders", "delivered",
                         "reassigned", "failed", "on_time_rate",
                         "avg_distance", "agents_busy", "cost_saved_inr"])
        for row in conn.execute("SELECT * FROM tick_snapshots ORDER BY tick"):
            writer.writerow(row[1:])

    conn.close()
    return "assignments_export.csv", "tick_history_export.csv"

# ── INIT ON IMPORT ────────────────────────────────────────────────────

init_db()