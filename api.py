import threading
import time
import json
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from scenario import set_scenario, get_scenario, get_current_config
from cities import set_city, get_city, get_current_city
from simulation import SimulationState
from engine import assign_orders, get_quality_metrics, score_agent_for_order, agent_can_take_order
from realtime import (
    move_agents, detect_and_reassign,
    inject_new_orders, MetricsTracker,
    TICK_INTERVAL, NEW_ORDER_RATE
)
from map_view import build_map
from utils import euclidean_distance, get_traffic_delay
from database import (
    log_tick_snapshot, log_event,
    get_tick_history, get_full_stats, export_to_csv
)
from optimizer import start_tuning, get_tuning_results
from forecaster import get_forecaster
from agent import start_agent, get_agent_state
from rl_engine import get_rl_agent, get_rl_status, start_training, assign_orders_rl
from anomaly import get_detector
from ab_testing import start_ab_test, get_ab_results

# ── GLOBAL STATE ──────────────────────────────────────────────────────

sim     = SimulationState()
metrics = MetricsTracker()
tick    = {"value": 0}
running = {"value": False}
_loop   = {"ref": None}

# ── WEBSOCKET CONNECTION MANAGER ──────────────────────────────────────

class ConnectionManager:
    def __init__(self):
        self.active: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)

    def disconnect(self, ws: WebSocket):
        if ws in self.active:
            self.active.remove(ws)

    async def broadcast(self, data: dict):
        dead = []
        for ws in self.active:
            try:
                await ws.send_text(json.dumps(data))
            except:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)

manager = ConnectionManager()

# ── WS PAYLOAD BUILDER ────────────────────────────────────────────────

def build_ws_payload():
    avg_dist, on_time, _ = get_quality_metrics(sim)

    BASELINE_AVG   = 52.51
    COST_PER_UNIT  = 12
    dist_saved     = max(BASELINE_AVG - avg_dist, 0)
    cost_saved     = round(dist_saved * COST_PER_UNIT * metrics.total_delivered)
    dist_saved_pct = round((dist_saved / max(BASELINE_AVG, 1)) * 100, 1)

    return {
        "type": "tick_update",
        "tick": tick["value"],
        "metrics": {
            "tick":              tick["value"],
            "total_orders":      len(sim.orders),
            "pending":           len([o for o in sim.orders if o.status == "pending"]),
            "assigned":          len([o for o in sim.orders if o.status == "assigned"]),
            "delivered":         len([o for o in sim.orders if o.status == "delivered"]),
            "failed":            len([o for o in sim.orders if o.status == "failed"]),
            "total_assigned":    metrics.total_assigned,
            "total_reassigned":  metrics.total_reassigned,
            "total_delivered":   metrics.total_delivered,
            "total_failed":      metrics.total_failed,
            "on_time_rate":      metrics.get_on_time_rate(),
            "avg_distance":      avg_dist,
            "agents_idle":       len([a for a in sim.agents if a.status == "idle"]),
            "agents_busy":       len([a for a in sim.agents if a.status == "busy"]),
            "dist_saved_pct":    dist_saved_pct,
            "cost_saved_inr":    cost_saved,
            "baseline_avg_dist": BASELINE_AVG,
        },
        "agents": [
            {
                "agent_id":       a.agent_id,
                "location":       a.location,
                "capacity":       a.capacity,
                "current_orders": a.current_orders,
                "status":         a.status,
                "load_pct":       round(len(a.current_orders) / a.capacity * 100)
            }
            for a in sim.agents
        ],
        "logs": list(reversed(metrics.decision_logs[-10:]))
    }

# ── BACKGROUND SIMULATION THREAD ─────────────────────────────────────

def simulation_loop():
    global sim, metrics

    assigned, skipped = assign_orders(sim, verbose=False)
    metrics.total_assigned += assigned

    while running["value"]:
        try:
            time.sleep(TICK_INTERVAL)
            tick["value"] += 1

            move_agents(sim, metrics)
            detect_and_reassign(sim, metrics)

            if tick["value"] % 2 == 0:
                inject_new_orders(sim, metrics, tick["value"])

            new_assigned, _ = assign_orders(sim, verbose=False)
            if new_assigned:
                metrics.total_assigned += new_assigned

            # ── record demand for forecaster ──
            get_forecaster().record(
                len([o for o in sim.orders if o.status == "pending"])
            )

            # ── log tick snapshot to SQLite ──
            try:
                avg_dist, on_time, _ = get_quality_metrics(sim)
                BASELINE_AVG = 52.51
                dist_saved   = max(BASELINE_AVG - avg_dist, 0)
                cost_saved   = round(dist_saved * 12 * metrics.total_delivered)
                log_tick_snapshot(
                    tick=tick["value"],
                    total_orders=len(sim.orders),
                    delivered=metrics.total_delivered,
                    reassigned=metrics.total_reassigned,
                    failed=metrics.total_failed,
                    on_time_rate=metrics.get_on_time_rate(),
                    avg_distance=avg_dist,
                    agents_busy=len([a for a in sim.agents if a.status == "busy"]),
                    cost_saved_inr=cost_saved
                )
            except Exception as e:
                print(f"[DB] Snapshot error: {e}")

            # ── anomaly detection every 3 ticks ──
            if tick["value"] % 3 == 0:
                get_detector().check(sim, metrics, tick["value"])

            # ── broadcast to WebSocket clients ──
            loop = _loop["ref"]
            if loop and loop.is_running() and manager.active:
                try:
                    asyncio.run_coroutine_threadsafe(
                        manager.broadcast(build_ws_payload()),
                        loop
                    )
                except Exception:
                    pass

        except Exception as e:
            import traceback
            print(f"[SIMULATION ERROR] Tick {tick['value']}: {e}")
            traceback.print_exc()

# ── LIFESPAN ──────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    _loop["ref"]     = asyncio.get_event_loop()
    running["value"] = True
    thread = threading.Thread(target=simulation_loop, daemon=True)
    thread.start()

    # start autonomous agent monitor
    from agent import start_auto_monitor
    start_auto_monitor(sim, metrics, tick, lambda mode: set_scenario(mode))

    yield
    running["value"] = False

# ── APP ───────────────────────────────────────────────────────────────

app = FastAPI(
    title="Fleet AI Decision Engine",
    description="Real-time autonomous dispatch system API",
    version="4.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── REST ENDPOINTS ────────────────────────────────────────────────────

@app.get("/")
def root():
    city = get_current_city()
    return {
        "system":  "Fleet AI Decision Engine",
        "status":  "running",
        "tick":    tick["value"],
        "clients": len(manager.active),
        "city":    city["name"]
    }

@app.get("/api/agents")
def get_agents():
    return [
        {
            "agent_id":       a.agent_id,
            "location":       a.location,
            "capacity":       a.capacity,
            "current_orders": a.current_orders,
            "status":         a.status,
            "load_pct":       round(len(a.current_orders) / a.capacity * 100)
        }
        for a in sim.agents
    ]

@app.get("/api/orders")
def get_orders():
    return [
        {
            "order_id":       o.order_id,
            "location":       o.location,
            "priority":       o.priority,
            "deadline":       round(o.deadline, 1),
            "status":         o.status,
            "assigned_agent": o.assigned_agent
        }
        for o in sim.orders
    ]

@app.get("/api/metrics")
def get_metrics():
    avg_dist, on_time, _ = get_quality_metrics(sim)

    pending   = len([o for o in sim.orders if o.status == "pending"])
    assigned  = len([o for o in sim.orders if o.status == "assigned"])
    delivered = len([o for o in sim.orders if o.status == "delivered"])
    failed    = len([o for o in sim.orders if o.status == "failed"])
    idle      = len([a for a in sim.agents if a.status == "idle"])
    busy      = len([a for a in sim.agents if a.status == "busy"])

    COST_PER_UNIT  = 12
    BASELINE_AVG   = 52.51
    dist_saved     = max(BASELINE_AVG - avg_dist, 0)
    cost_saved     = round(dist_saved * COST_PER_UNIT * metrics.total_delivered)
    dist_saved_pct = round((dist_saved / max(BASELINE_AVG, 1)) * 100, 1)

    return {
        "tick":              tick["value"],
        "total_orders":      len(sim.orders),
        "pending":           pending,
        "assigned":          assigned,
        "delivered":         delivered,
        "failed":            failed,
        "total_assigned":    metrics.total_assigned,
        "total_reassigned":  metrics.total_reassigned,
        "total_delivered":   metrics.total_delivered,
        "total_failed":      metrics.total_failed,
        "on_time_rate":      metrics.get_on_time_rate(),
        "avg_distance":      avg_dist,
        "agents_idle":       idle,
        "agents_busy":       busy,
        "dist_saved_pct":    dist_saved_pct,
        "cost_saved_inr":    cost_saved,
        "baseline_avg_dist": BASELINE_AVG,
    }

@app.get("/api/logs")
def get_logs():
    last_20 = metrics.decision_logs[-20:]
    return {
        "total_logs": len(metrics.decision_logs),
        "logs":       list(reversed(last_20))
    }

@app.get("/api/status")
def get_status():
    return {
        "running":    running["value"],
        "tick":       tick["value"],
        "agents":     len(sim.agents),
        "orders":     len(sim.orders),
        "uptime_s":   tick["value"] * TICK_INTERVAL,
        "ws_clients": len(manager.active)
    }

@app.get("/api/map")
def get_map():
    m = build_map(sim)
    return {"html": m._repr_html_()}

@app.get("/api/explain/{order_id}")
def explain_assignment(order_id: int):
    order = sim.get_order_by_id(order_id)
    if not order:
        return {"error": "Order not found"}

    candidates = []
    for agent in sim.agents:
        dist        = euclidean_distance(agent.location, order.location)
        delay       = get_traffic_delay(agent.location, sim.traffic_zones)
        est_time    = dist * delay * 0.5
        can, reason = agent_can_take_order(agent, order, sim.traffic_zones)
        score       = score_agent_for_order(agent, order, sim.traffic_zones) if can else 0

        candidates.append({
            "agent_id":    agent.agent_id,
            "distance":    round(dist, 2),
            "delay":       round(delay, 2),
            "est_time":    round(est_time, 2),
            "capacity":    agent.capacity,
            "load":        len(agent.current_orders),
            "score":       round(score, 4),
            "eligible":    can,
            "reason":      reason,
            "is_assigned": agent.agent_id == order.assigned_agent
        })

    candidates.sort(key=lambda x: -x["score"])

    return {
        "order_id":       order.order_id,
        "order_location": order.location,
        "priority":       order.priority,
        "deadline":       round(order.deadline, 1),
        "status":         order.status,
        "assigned_agent": order.assigned_agent,
        "candidates":     candidates[:5]
    }

# ── DB ENDPOINTS ──────────────────────────────────────────────────────

@app.get("/api/history")
def get_history():
    rows = get_tick_history(100)
    return [
        {
            "tick":         r[0],
            "on_time_rate": r[1],
            "avg_distance": r[2],
            "delivered":    r[3],
            "reassigned":   r[4],
            "agents_busy":  r[5],
            "cost_saved":   r[6]
        }
        for r in rows
    ]

@app.get("/api/stats")
def get_stats():
    return get_full_stats()

@app.get("/api/export")
def export_data():
    f1, f2 = export_to_csv()
    return {"message": "Exported successfully", "files": [f1, f2]}

# ── SCENARIO ENDPOINTS ────────────────────────────────────────────────

@app.get("/api/scenario")
def scenario_status():
    return get_scenario()

@app.post("/api/scenario/{mode}")
def change_scenario(mode: str):
    result = set_scenario(mode)
    if "error" in result:
        return result
    metrics.log(f"SCENARIO  Changed to {result['scenario']['name']} {result['scenario']['emoji']}")
    return result

# ── CITY ENDPOINTS ────────────────────────────────────────────────────

@app.get("/api/city")
def city_status():
    return get_city()

@app.post("/api/city/{city_key}")
def change_city(city_key: str):
    global sim, metrics, tick
    result = set_city(city_key)
    if "error" in result:
        return result

    sim                        = SimulationState()
    assigned, _                = assign_orders(sim, verbose=False)
    metrics.total_assigned     = assigned
    metrics.total_delivered    = 0
    metrics.total_reassigned   = 0
    metrics.total_failed       = 0
    metrics.on_time_deliveries = 0
    metrics.decision_logs      = []
    tick["value"]              = 0

    city = result["city"]
    metrics.log(f"CITY  Switched to {city['emoji']} {city['name']} | {city['agents']} agents | {city['orders']} orders")
    return result

# ── FORECAST ENDPOINTS ────────────────────────────────────────────────

@app.get("/api/forecast")
def get_forecast():
    return get_forecaster().get_summary()

# ── AGENT ENDPOINTS ───────────────────────────────────────────────────

@app.get("/api/agent")
def agent_state():
    return get_agent_state()

@app.post("/api/agent/run")
def run_agent_now():
    return start_agent(sim, metrics, tick, lambda mode: set_scenario(mode))

# ── TUNING ENDPOINTS ──────────────────────────────────────────────────

@app.get("/api/tuning")
def get_tuning():
    return get_tuning_results()

@app.post("/api/tuning/start")
def start_weight_tuning():
    return start_tuning()

# ── RL ENDPOINTS ──────────────────────────────────────────────────────

@app.get("/api/rl/status")
def rl_status():
    return get_rl_status()

@app.post("/api/rl/train")
def rl_train(episodes: int = 50):
    return start_training(episodes)

@app.post("/api/rl/assign")
def rl_assign_now():
    agent             = get_rl_agent()
    assigned, skipped = assign_orders_rl(sim, agent, training=False)
    return {
        "assigned": assigned,
        "skipped":  skipped,
        "stats":    agent.get_stats()
    }

# ── ANOMALY ENDPOINTS ─────────────────────────────────────────────────

@app.get("/api/anomalies")
def get_anomalies():
    return get_detector().get_summary()

# ── A/B TESTING ENDPOINTS ─────────────────────────────────────────────

@app.get("/api/ab/results")
def ab_results():
    return get_ab_results()

@app.post("/api/ab/run")
def ab_run(ticks: int = 20):
    return start_ab_test(ticks)

# --- React map component ------------------------------------------------------
@app.get("/api/routes")
def get_routes():
    from map_view import grid_to_latlon
    routes = []
    for agent in sim.agents:
        if not agent.current_orders:
            continue
        order = sim.get_order_by_id(agent.current_orders[0])
        if not order:
            continue
        a_lat, a_lon = grid_to_latlon(*agent.location)
        o_lat, o_lon = grid_to_latlon(*order.location)
        routes.append({
            "agent_id":    agent.agent_id,
            "agent_lat":   a_lat,
            "agent_lon":   a_lon,
            "order_id":    order.order_id,
            "order_lat":   o_lat,
            "order_lon":   o_lon,
            "priority":    order.priority,
            "status":      agent.status,
            "load_pct":    round(len(agent.current_orders) / agent.capacity * 100)
        })
    return routes

# ── NLP QUERY ENDPOINT ────────────────────────────────────────────────

@app.post("/api/query")
async def natural_language_query(request: Request):
    import google.generativeai as genai

    body  = await request.json()
    query = body.get("query", "")

    if not query:
        return {"answer": "Please ask a question.", "tick": tick["value"]}

    avg_dist, on_time, _ = get_quality_metrics(sim)
    city      = get_current_city()
    pending   = len([o for o in sim.orders if o.status == "pending"])
    assigned  = len([o for o in sim.orders if o.status == "assigned"])
    delivered = len([o for o in sim.orders if o.status == "delivered"])
    failed    = len([o for o in sim.orders if o.status == "failed"])
    busy      = len([a for a in sim.agents if a.status == "busy"])
    idle      = len([a for a in sim.agents if a.status == "idle"])
    busiest   = max(sim.agents, key=lambda a: len(a.current_orders))
    recent_logs = metrics.decision_logs[-5:]

    context = f"""
You are an AI assistant for a real-time fleet dispatch system.

LIVE SYSTEM STATE:
- City: {city['name']}
- Tick: {tick['value']}
- On-Time Rate: {on_time}%
- Avg Distance: {avg_dist}u
- Total Orders: {len(sim.orders)}
- Pending: {pending} | Assigned: {assigned} | Delivered: {delivered} | Failed: {failed}
- Agents Busy: {busy} | Agents Idle: {idle}
- Total Reassignments: {metrics.total_reassigned}
- Busiest Agent: Agent {busiest.agent_id} with {len(busiest.current_orders)}/{busiest.capacity} orders
- Recent Events: {recent_logs}

Answer the user's question concisely and accurately in under 3 sentences.
If asked for a recommendation, give one based on the live data above.
"""

    try:
        genai.configure(api_key="GEMINI_API_KEY")
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(context + f"\n\nUser Question: {query}")
        return {"answer": response.text, "tick": tick["value"]}
    except Exception as e:
        return {"answer": f"Query error: {str(e)}", "tick": tick["value"]}

# ── WEBSOCKET ENDPOINT ────────────────────────────────────────────────

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await manager.connect(ws)
    try:
        await ws.send_text(json.dumps(build_ws_payload()))
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(ws)
