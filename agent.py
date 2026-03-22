import time
import threading
import json
import google.generativeai as genai

# ── CONFIGURE GEMINI ──────────────────────────────────────────────────

GEMINI_API_KEY = "AIzaSyA4DS3_7kTKlLdmC-gQG-VKfdQjRDkuBXM"
genai.configure(api_key=GEMINI_API_KEY)

# ── AGENT MEMORY ──────────────────────────────────────────────────────

agent_memory = {
    "observations": [],
    "actions":      [],
    "reports":      [],
    "status":       "idle",
    "last_run":     None
}

# ── DATA COLLECTOR ────────────────────────────────────────────────────

def collect_system_state(sim_ref, metrics_ref, tick_ref):
    from engine import get_quality_metrics
    from utils import euclidean_distance, get_traffic_delay

    avg_dist, on_time, _ = get_quality_metrics(sim_ref)

    at_risk = []
    for order in sim_ref.orders:
        if order.status != "assigned":
            continue
        agent = sim_ref.get_agent_by_id(order.assigned_agent)
        if agent:
            dist     = euclidean_distance(agent.location, order.location)
            delay    = get_traffic_delay(agent.location, sim_ref.traffic_zones)
            est_time = dist * delay * 0.5
            if est_time > order.deadline * 0.8:
                at_risk.append(order.order_id)

    recent_logs = metrics_ref.decision_logs[-10:]

    return {
        "tick":            tick_ref["value"],
        "on_time_rate":    metrics_ref.get_on_time_rate(),
        "avg_distance":    round(avg_dist, 2),
        "total_orders":    len(sim_ref.orders),
        "pending":         len([o for o in sim_ref.orders if o.status == "pending"]),
        "assigned":        len([o for o in sim_ref.orders if o.status == "assigned"]),
        "delivered":       metrics_ref.total_delivered,
        "failed":          metrics_ref.total_failed,
        "reassignments":   metrics_ref.total_reassigned,
        "agents_busy":     len([a for a in sim_ref.agents if a.status == "busy"]),
        "agents_idle":     len([a for a in sim_ref.agents if a.status == "idle"]),
        "at_risk_orders":  len(at_risk),
        "recent_logs":     recent_logs[-5:]
    }

# ── GEMINI AGENT ──────────────────────────────────────────────────────

def run_agent(sim_ref, metrics_ref, tick_ref, scenario_setter):
    agent_memory["status"]   = "running"
    agent_memory["last_run"] = time.strftime("%H:%M:%S")

    try:
        state = collect_system_state(sim_ref, metrics_ref, tick_ref)

        prompt = f"""You are an autonomous AI operations agent monitoring a real-time fleet dispatch system in Bangalore, India.

CURRENT SYSTEM STATE (Tick {state['tick']}):
- On-Time Rate: {state['on_time_rate']}%
- Avg Distance: {state['avg_distance']}u
- Total Orders: {state['total_orders']}
- Pending: {state['pending']} | Assigned: {state['assigned']} | Delivered: {state['delivered']} | Failed: {state['failed']}
- Reassignments: {state['reassignments']}
- Agents Busy: {state['agents_busy']} | Agents Idle: {state['agents_idle']}
- Orders at SLA Risk: {state['at_risk_orders']}
- Recent Events: {json.dumps(state['recent_logs'][-3:], indent=2)}

AVAILABLE SCENARIOS:
- normal: Standard conditions (3 orders/tick, speed 2.0)
- rush_hour: Heavy load (8 orders/tick, speed 1.2, traffic 2.5x)
- low_demand: Light load (1 order/tick, speed 3.5, traffic 0.5x)
- chaos: Maximum stress (12 orders/tick, speed 0.8, traffic 4.0x)

YOUR TASK:
1. Analyze the system state thoroughly
2. Identify any problems or opportunities
3. Decide whether to change the scenario (or keep current)
4. Explain your reasoning step by step

RESPOND IN THIS EXACT JSON FORMAT:
{{
  "analysis": "Your detailed analysis of the system state",
  "problems_detected": ["list", "of", "problems"],
  "recommendation": "normal" or "rush_hour" or "low_demand" or "chaos" or "no_change",
  "reasoning": "Why you made this recommendation",
  "severity": "healthy" or "warning" or "critical",
  "report": "A 2-3 sentence operations summary"
}}

Respond ONLY with valid JSON, no other text."""

        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt)
        raw      = response.text.strip()

        # clean markdown fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()

        decision = json.loads(raw)
        print(f"[AGENT] Gemini response: {decision}")

        # log observation
        agent_memory["observations"].append({
            "tick":     state["tick"],
            "text":     f"[{decision['severity'].upper()}] {decision['analysis']} — {decision['reasoning']}",
            "time":     time.strftime("%H:%M:%S"),
            "severity": decision["severity"]
        })

        # execute recommendation
        if decision["recommendation"] != "no_change":
            scenario_setter(decision["recommendation"])
            metrics_ref.log(
                f"AGENT  Gemini AI switched to {decision['recommendation'].upper()} — "
                f"{decision['reasoning'][:80]}"
            )
            agent_memory["actions"].append({
                "action": f"Changed scenario to {decision['recommendation']}",
                "reason": decision["reasoning"],
                "tick":   state["tick"],
                "time":   time.strftime("%H:%M:%S")
            })
        else:
            metrics_ref.log(f"AGENT  Gemini AI: No intervention — {decision['report'][:80]}")

        # store report
        agent_memory["reports"].append({
            "tick":     state["tick"],
            "time":     time.strftime("%H:%M:%S"),
            "severity": decision["severity"],
            "report":   decision["report"],
            "problems": decision["problems_detected"],
            "action":   decision["recommendation"]
        })

        agent_memory["status"] = "complete"

    except json.JSONDecodeError as e:
        print(f"[AGENT] JSON parse error: {e} — using fallback")
        _fallback_agent(sim_ref, metrics_ref, tick_ref, scenario_setter)

    except Exception as e:
        print(f"[AGENT ERROR] {e}")
        import traceback
        traceback.print_exc()
        _fallback_agent(sim_ref, metrics_ref, tick_ref, scenario_setter)

# ── FALLBACK RULE-BASED AGENT ─────────────────────────────────────────

def _fallback_agent(sim_ref, metrics_ref, tick_ref, scenario_setter):
    """Used if Gemini fails — rule-based decisions."""
    from engine import get_quality_metrics
    avg_dist, on_time, _ = get_quality_metrics(sim_ref)
    pending = len([o for o in sim_ref.orders if o.status == "pending"])

    if on_time < 80:
        scenario_setter("normal")
        action = f"Fallback: switched to NORMAL — on-time {on_time}% critical"
    elif pending > 40:
        scenario_setter("low_demand")
        action = f"Fallback: switched to LOW DEMAND — {pending} orders backlogged"
    elif on_time >= 95 and pending < 5:
        action = "Fallback: system healthy — no intervention needed"
    else:
        action = f"Fallback: monitoring — on-time {on_time}%, pending {pending}"

    agent_memory["observations"].append({
        "tick":     tick_ref["value"],
        "text":     action,
        "time":     time.strftime("%H:%M:%S"),
        "severity": "warning" if on_time < 80 else "healthy"
    })
    agent_memory["status"] = "complete"

# ── AUTO MONITOR ──────────────────────────────────────────────────────

def start_auto_monitor(sim_ref, metrics_ref, tick_ref, scenario_setter):
    """Runs Gemini agent automatically every 15 ticks."""
    def monitor_loop():
        last_tick = 0
        while True:
            time.sleep(3)
            current = tick_ref["value"]
            if current - last_tick >= 15 and current > 5:
                last_tick = current
                if agent_memory["status"] != "running":
                    print(f"[AGENT] Auto-monitor at tick {current}")
                    run_agent(sim_ref, metrics_ref, tick_ref, scenario_setter)

    threading.Thread(target=monitor_loop, daemon=True).start()

# ── PUBLIC API ────────────────────────────────────────────────────────

def start_agent(sim_ref, metrics_ref, tick_ref, scenario_setter):
    if agent_memory["status"] == "running":
        return {"status": "already_running"}
    threading.Thread(
        target=run_agent,
        args=(sim_ref, metrics_ref, tick_ref, scenario_setter),
        daemon=True
    ).start()
    return {"status": "started"}

def get_agent_state():
    return {
        "status":        agent_memory["status"],
        "last_run":      agent_memory["last_run"],
        "observations":  agent_memory["observations"][-5:],
        "actions":       agent_memory["actions"][-5:],
        "reports":       agent_memory["reports"][-3:],
        "total_obs":     len(agent_memory["observations"]),
        "total_actions": len(agent_memory["actions"])
    }

