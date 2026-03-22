# ── SCENARIO CONFIGS ──────────────────────────────────────────────────

SCENARIOS = {
    "normal": {
        "name":           "Normal",
        "description":    "Standard operating conditions",
        "tick_interval":  3,
        "new_order_rate": 3,
        "agent_speed":    2.0,
        "traffic_multiplier": 1.0,
        "emoji":          "🟢"
    },
    "rush_hour": {
        "name":           "Rush Hour",
        "description":    "5x orders, heavy traffic delays",
        "tick_interval":  3,
        "new_order_rate": 8,
        "agent_speed":    1.2,
        "traffic_multiplier": 2.5,
        "emoji":          "🔴"
    },
    "low_demand": {
        "name":           "Low Demand",
        "description":    "Sparse orders, clear roads",
        "tick_interval":  3,
        "new_order_rate": 1,
        "agent_speed":    3.5,
        "traffic_multiplier": 0.5,
        "emoji":          "🔵"
    },
    "chaos": {
        "name":           "Chaos Mode",
        "description":    "Max orders, max traffic, agents slow",
        "tick_interval":  3,
        "new_order_rate": 12,
        "agent_speed":    0.8,
        "traffic_multiplier": 4.0,
        "emoji":          "🟡"
    }
}

# active scenario state
current_scenario = {"key": "normal", "config": SCENARIOS["normal"]}

def set_scenario(key: str) -> dict:
    if key not in SCENARIOS:
        return {"error": f"Unknown scenario: {key}"}
    current_scenario["key"]    = key
    current_scenario["config"] = SCENARIOS[key]
    return {"status": "ok", "scenario": SCENARIOS[key]}

def get_scenario() -> dict:
    return {
        "current": current_scenario["key"],
        "config":  current_scenario["config"],
        "all":     SCENARIOS
    }

def get_current_config() -> dict:
    return current_scenario["config"]