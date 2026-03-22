import threading
from simulation import SimulationState
from engine import assign_orders, get_quality_metrics
from realtime import move_agents, detect_and_reassign, inject_new_orders, MetricsTracker
import engine as eng

# ── WEIGHT COMBINATIONS TO TEST ───────────────────────────────────────

WEIGHT_COMBINATIONS = [
    {"W_PROXIMITY": 0.5, "W_CAPACITY": 0.2, "W_URGENCY": 0.2, "W_DEADLINE": 0.1},
    {"W_PROXIMITY": 0.6, "W_CAPACITY": 0.1, "W_URGENCY": 0.2, "W_DEADLINE": 0.1},
    {"W_PROXIMITY": 0.4, "W_CAPACITY": 0.2, "W_URGENCY": 0.3, "W_DEADLINE": 0.1},
    {"W_PROXIMITY": 0.3, "W_CAPACITY": 0.3, "W_URGENCY": 0.3, "W_DEADLINE": 0.1},
    {"W_PROXIMITY": 0.5, "W_CAPACITY": 0.1, "W_URGENCY": 0.3, "W_DEADLINE": 0.1},
    {"W_PROXIMITY": 0.4, "W_CAPACITY": 0.3, "W_URGENCY": 0.2, "W_DEADLINE": 0.1},
    {"W_PROXIMITY": 0.6, "W_CAPACITY": 0.2, "W_URGENCY": 0.1, "W_DEADLINE": 0.1},
    {"W_PROXIMITY": 0.3, "W_CAPACITY": 0.2, "W_URGENCY": 0.4, "W_DEADLINE": 0.1},
    {"W_PROXIMITY": 0.5, "W_CAPACITY": 0.2, "W_URGENCY": 0.1, "W_DEADLINE": 0.2},
    {"W_PROXIMITY": 0.4, "W_CAPACITY": 0.1, "W_URGENCY": 0.3, "W_DEADLINE": 0.2},
]

# ── FAST SIMULATION ───────────────────────────────────────────────────

def run_fast_simulation(weights, ticks=8):
    """Run a quick simulation with patched weights and return metrics."""
    # patch engine module weights
    eng.W_PROXIMITY = weights["W_PROXIMITY"]
    eng.W_CAPACITY  = weights["W_CAPACITY"]
    eng.W_URGENCY   = weights["W_URGENCY"]
    eng.W_DEADLINE  = weights["W_DEADLINE"]

    sim     = SimulationState()
    metrics = MetricsTracker()
    assign_orders(sim, verbose=False)

    for tick in range(1, ticks + 1):
        move_agents(sim, metrics)
        detect_and_reassign(sim, metrics)
        if tick % 2 == 0:
            inject_new_orders(sim, metrics, tick)
        assign_orders(sim, verbose=False)

    avg_dist, on_time, _ = get_quality_metrics(sim)

    # composite score: on-time rate weighted 60%, distance improvement 40%
    score = round(
        metrics.get_on_time_rate() * 0.6 +
        max(0, (52.51 - avg_dist)) * 0.4,
        2
    )

    return {
        "weights":      weights,
        "on_time_rate": metrics.get_on_time_rate(),
        "avg_distance": round(avg_dist, 2),
        "delivered":    metrics.total_delivered,
        "reassigned":   metrics.total_reassigned,
        "score":        score
    }

# ── GRID SEARCH ───────────────────────────────────────────────────────

def run_grid_search():
    results = []
    for i, weights in enumerate(WEIGHT_COMBINATIONS):
        print(f"[TUNER] Testing {i+1}/{len(WEIGHT_COMBINATIONS)}: {weights}")
        result = run_fast_simulation(weights)
        results.append(result)

    # restore default weights
    eng.W_PROXIMITY = 0.5
    eng.W_CAPACITY  = 0.2
    eng.W_URGENCY   = 0.2
    eng.W_DEADLINE  = 0.1

    results.sort(key=lambda x: -x["score"])
    return results

# ── STATE ─────────────────────────────────────────────────────────────

tuning_results = {"results": [], "best": None, "status": "idle"}

def get_tuning_results():
    return tuning_results

def start_tuning():
    if tuning_results["status"] == "running":
        return {"status": "already_running"}

    tuning_results["status"]  = "running"
    tuning_results["results"] = []
    tuning_results["best"]    = None

    def run():
        results = run_grid_search()
        tuning_results["results"] = results
        tuning_results["best"]    = results[0] if results else None
        tuning_results["status"]  = "complete"
        if results:
            print(f"[TUNER] Best: {results[0]['weights']} | Score: {results[0]['score']}")

    threading.Thread(target=run, daemon=True).start()
    return {"status": "started", "combos": len(WEIGHT_COMBINATIONS)}