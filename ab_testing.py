import time
import threading
from collections import defaultdict

# ── A/B TEST STATE ────────────────────────────────────────────────────

ab_state = {
    "running":    False,
    "results":    {},
    "history":    [],
    "start_tick": 0,
    "status":     "idle"
}

# ── METRICS COLLECTOR ─────────────────────────────────────────────────

class EngineMetrics:
    def __init__(self, name):
        self.name          = name
        self.assigned      = 0
        self.delivered     = 0
        self.failed        = 0
        self.reassigned    = 0
        self.total_dist    = 0.0
        self.on_time       = 0
        self.tick_snapshots= []

    def record_snapshot(self, tick, on_time_rate, avg_dist, delivered):
        self.tick_snapshots.append({
            "tick":         tick,
            "on_time_rate": on_time_rate,
            "avg_distance": round(avg_dist, 2),
            "delivered":    delivered
        })

    def get_summary(self):
        snaps    = self.tick_snapshots
        avg_ot   = round(sum(s["on_time_rate"] for s in snaps) / max(len(snaps), 1), 1)
        avg_dist = round(sum(s["avg_distance"]  for s in snaps) / max(len(snaps), 1), 2)
        return {
            "name":          self.name,
            "avg_on_time":   avg_ot,
            "avg_distance":  avg_dist,
            "total_assigned": self.assigned,
            "total_delivered": self.delivered,
            "total_failed":  self.failed,
            "snapshots":     snaps[-10:]
        }

# ── A/B TEST RUNNER ───────────────────────────────────────────────────

def run_ab_test(ticks=20):
    """
    Run greedy vs RL side by side on identical simulation conditions.
    Both engines get the same starting state, same orders, same agents.
    """
    from simulation import SimulationState
    from engine import assign_orders, get_quality_metrics
    from rl_engine import assign_orders_rl, get_rl_agent
    from realtime import move_agents, detect_and_reassign, inject_new_orders, MetricsTracker

    ab_state["status"]  = "running"
    ab_state["running"] = True

    print(f"[A/B] Starting test — {ticks} ticks each")

    # ── run greedy engine ──
    greedy_metrics_obj = EngineMetrics("Greedy")
    sim_g   = SimulationState()
    met_g   = MetricsTracker()
    assign_orders(sim_g, verbose=False)

    for tick in range(1, ticks + 1):
        move_agents(sim_g, met_g)
        detect_and_reassign(sim_g, met_g)
        if tick % 2 == 0:
            inject_new_orders(sim_g, met_g, tick)
        assign_orders(sim_g, verbose=False)

        avg_dist, on_time, _ = get_quality_metrics(sim_g)
        greedy_metrics_obj.record_snapshot(tick, met_g.get_on_time_rate(), avg_dist, met_g.total_delivered)

    greedy_metrics_obj.assigned  = len([o for o in sim_g.orders if o.status in ["assigned","delivered"]])
    greedy_metrics_obj.delivered = met_g.total_delivered
    greedy_metrics_obj.failed    = met_g.total_failed
    greedy_metrics_obj.reassigned= met_g.total_reassigned

    print(f"[A/B] Greedy done — on-time: {met_g.get_on_time_rate()}%")

    # ── run RL engine ──
    rl_metrics_obj = EngineMetrics("RL Agent")
    rl_agent = get_rl_agent()
    sim_r    = SimulationState()
    met_r    = MetricsTracker()
    assign_orders_rl(sim_r, rl_agent, training=False)

    for tick in range(1, ticks + 1):
        move_agents(sim_r, met_r)
        detect_and_reassign(sim_r, met_r)
        if tick % 2 == 0:
            inject_new_orders(sim_r, met_r, tick)
        assign_orders_rl(sim_r, rl_agent, training=False)

        avg_dist, on_time, _ = get_quality_metrics(sim_r)
        rl_metrics_obj.record_snapshot(tick, met_r.get_on_time_rate(), avg_dist, met_r.total_delivered)

    rl_metrics_obj.assigned  = len([o for o in sim_r.orders if o.status in ["assigned","delivered"]])
    rl_metrics_obj.delivered = met_r.total_delivered
    rl_metrics_obj.failed    = met_r.total_failed
    rl_metrics_obj.reassigned= met_r.total_reassigned

    print(f"[A/B] RL done — on-time: {met_r.get_on_time_rate()}%")

    # ── compute winner ──
    g_summary = greedy_metrics_obj.get_summary()
    r_summary = rl_metrics_obj.get_summary()

    winner = "Greedy" if g_summary["avg_on_time"] >= r_summary["avg_on_time"] else "RL Agent"
    if abs(g_summary["avg_on_time"] - r_summary["avg_on_time"]) < 2:
        winner = "Tie"

    ab_state["results"] = {
        "greedy":     g_summary,
        "rl":         r_summary,
        "winner":     winner,
        "ticks":      ticks,
        "completed":  time.strftime("%H:%M:%S"),
        "improvement": {
            "on_time_diff":  round(r_summary["avg_on_time"]  - g_summary["avg_on_time"],  1),
            "distance_diff": round(g_summary["avg_distance"] - r_summary["avg_distance"], 2)
        }
    }

    ab_state["history"].append(ab_state["results"].copy())
    ab_state["status"]  = "complete"
    ab_state["running"] = False
    print(f"[A/B] Complete — Winner: {winner}")

def start_ab_test(ticks=20):
    if ab_state["running"]:
        return {"status": "already_running"}
    ab_state["status"] = "running"
    threading.Thread(target=run_ab_test, args=(ticks,), daemon=True).start()
    return {"status": "started", "ticks": ticks}

def get_ab_results():
    return {
        "status":  ab_state["status"],
        "results": ab_state["results"],
        "history": ab_state["history"][-5:]
    }