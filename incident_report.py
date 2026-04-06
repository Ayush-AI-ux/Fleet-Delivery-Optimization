import time
import threading
import json
from google import genai
import os
from dotenv import load_dotenv

# Load environment (so it can access GEMINI_API_KEY)
load_dotenv()

# Use the same client as agent.py for consistency
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# ── REPORT STORE ──────────────────────────────────────────────────────

report_store = {
    "reports":    [],
    "generating": False,
    "last_generated": None
}

# ── REPORT GENERATOR ──────────────────────────────────────────────────

def generate_incident_report(sim_ref, metrics_ref, tick_ref, anomaly_ref=None):
    """Generate a Gemini-powered operations report for the current session."""
    from engine import get_quality_metrics
    from cities import get_current_city
    from scenario import get_current_config

    report_store["generating"] = True

    try:
        avg_dist, on_time, _ = get_quality_metrics(sim_ref)
        city     = get_current_city()
        scenario = get_current_config()

        # collect anomaly summary
        anomaly_summary = "No anomalies detected."
        if anomaly_ref:
            data = anomaly_ref.get_summary()
            if data["total"] > 0:
                anomaly_summary = (
                    f"{data['total']} anomalies detected — "
                    f"{data['critical_count']} critical, "
                    f"{data['warning_count']} warnings. "
                    f"Recent: {data['recent'][-1]['message'] if data['recent'] else 'N/A'}"
                )

        # collect recent logs
        recent_logs = metrics_ref.decision_logs[-10:]

        # build prompt
        prompt = f"""You are an AI operations analyst for a real-time fleet dispatch system.
Generate a professional incident report for the following simulation session.

SESSION DATA:
- City: {city['name']}
- Scenario: {scenario['name']}
- Duration: {tick_ref['value']} ticks ({tick_ref['value'] * 3} seconds)
- Total Orders: {len(sim_ref.orders)}
- Delivered: {metrics_ref.total_delivered}
- Failed: {metrics_ref.total_failed}
- Reassignments: {metrics_ref.total_reassigned}
- On-Time Rate: {metrics_ref.get_on_time_rate()}%
- Avg Distance: {avg_dist}u
- Agents: {len(sim_ref.agents)}
- Anomalies: {anomaly_summary}
- Recent Events: {json.dumps(recent_logs[-5:], indent=2)}

Write a professional 200-250 word operations report with these sections:
1. EXECUTIVE SUMMARY (2 sentences)
2. PERFORMANCE ANALYSIS (3-4 sentences with specific numbers)
3. INCIDENTS & INTERVENTIONS (2-3 sentences about SLA breaches and reassignments)
4. RECOMMENDATIONS (2-3 actionable recommendations)

Use professional fleet operations language. Be specific with numbers. Format with clear section headers."""

        # === NEW SDK ===
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        report = {
            "id":          len(report_store["reports"]) + 1,
            "timestamp":   time.strftime("%Y-%m-%d %H:%M:%S"),
            "tick":        tick_ref["value"],
            "city":        city["name"],
            "scenario":    scenario["name"],
            "on_time":     metrics_ref.get_on_time_rate(),
            "delivered":   metrics_ref.total_delivered,
            "reassigned":  metrics_ref.total_reassigned,
            "failed":      metrics_ref.total_failed,
            "avg_distance": round(avg_dist, 2),
            "content":     response.text,
            "status":      "complete"
        }

        report_store["reports"].append(report)
        report_store["last_generated"] = time.strftime("%H:%M:%S")
        report_store["generating"]     = False

        print(f"[REPORT] Generated report #{report['id']} for tick {tick_ref['value']}")
        return report

    except Exception as e:
        print(f"[REPORT ERROR] {e}")
        report_store["generating"] = False

        # fallback rule-based report
        from engine import get_quality_metrics
        avg_dist, on_time, _ = get_quality_metrics(sim_ref)

        report = {
            "id":        len(report_store["reports"]) + 1,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "tick":      tick_ref["value"],
            "city":      get_current_city()["name"],
            "scenario":  get_current_config()["name"],
            "on_time":   metrics_ref.get_on_time_rate(),
            "delivered": metrics_ref.total_delivered,
            "reassigned":metrics_ref.total_reassigned,
            "failed":    metrics_ref.total_failed,
            "avg_distance": round(avg_dist, 2),
            "content": f"""EXECUTIVE SUMMARY
Fleet operations completed {tick_ref['value']} ticks with {metrics_ref.get_on_time_rate()}% on-time delivery rate across {len(sim_ref.orders)} total orders.

PERFORMANCE ANALYSIS
The system delivered {metrics_ref.total_delivered} orders successfully with an average distance of {round(avg_dist,2)}u per delivery. A total of {metrics_ref.total_failed} orders failed to meet deadline constraints. The constraint-aware greedy engine maintained efficient agent utilization throughout the session.

INCIDENTS & INTERVENTIONS
{metrics_ref.total_reassigned} SLA breach interventions were executed by the real-time reassignment engine. Each reassignment was triggered when estimated arrival time exceeded the order deadline buffer, and a suitable replacement agent was identified and dispatched.

RECOMMENDATIONS
1. {'Switch to Low Demand mode to clear backlog.' if metrics_ref.total_failed > 5 else 'Current scenario is well-handled — consider Rush Hour for stress testing.'}
2. {'Consider increasing agent count for better coverage.' if metrics_ref.get_on_time_rate() < 90 else 'On-time rate is excellent — maintain current configuration.'}
3. Run weight auto-tuner to optimize scoring weights for current city traffic patterns.""",
            "status": "fallback"
        }

        report_store["reports"].append(report)
        report_store["last_generated"] = time.strftime("%H:%M:%S")
        return report

def start_report_generation(sim_ref, metrics_ref, tick_ref, anomaly_ref=None):
    if report_store["generating"]:
        return {"status": "already_generating"}
    threading.Thread(
        target=generate_incident_report,
        args=(sim_ref, metrics_ref, tick_ref, anomaly_ref),
        daemon=True
    ).start()
    return {"status": "started"}

def get_reports():
    return {
        "generating":     report_store["generating"],
        "last_generated": report_store["last_generated"],
        "total":          len(report_store["reports"]),
        "reports":        list(reversed(report_store["reports"]))[:5]
    }