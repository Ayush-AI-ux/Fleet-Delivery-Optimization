import time
from collections import deque

# ── ANOMALY DETECTOR ──────────────────────────────────────────────────

class AnomalyDetector:
    def __init__(self):
        self.on_time_history    = deque(maxlen=20)
        self.distance_history   = deque(maxlen=20)
        self.breach_history     = deque(maxlen=20)
        self.demand_history     = deque(maxlen=20)
        self.anomalies          = []
        self.last_check         = 0

    # ── STATISTICAL HELPERS ───────────────────────────────────────────

    def _mean(self, data):
        return sum(data) / len(data) if data else 0

    def _std(self, data):
        if len(data) < 2:
            return 0
        m   = self._mean(data)
        var = sum((x - m) ** 2 for x in data) / len(data)
        return var ** 0.5

    def _zscore(self, value, data):
        std = self._std(data)
        if std == 0:
            return 0
        return abs(value - self._mean(data)) / std

    # ── ANOMALY RULES ─────────────────────────────────────────────────

    def check(self, sim_ref, metrics_ref, tick):
        from engine import get_quality_metrics
        from utils import euclidean_distance, get_traffic_delay

        avg_dist, on_time, _ = get_quality_metrics(sim_ref)
        pending   = len([o for o in sim_ref.orders if o.status == "pending"])
        failed    = metrics_ref.total_failed
        reassigned= metrics_ref.total_reassigned

        # record history
        self.on_time_history.append(on_time)
        self.distance_history.append(avg_dist)
        self.breach_history.append(reassigned)
        self.demand_history.append(pending)

        detected = []

        # need at least 5 ticks of history
        if len(self.on_time_history) < 5:
            return detected

        # ── RULE 1: On-time rate sudden drop ──
        if len(self.on_time_history) >= 5:
            recent_avg = self._mean(list(self.on_time_history)[-3:])
            prev_avg   = self._mean(list(self.on_time_history)[-8:-3])
            if prev_avg > 0 and recent_avg < prev_avg * 0.85:
                detected.append({
                    "type":     "on_time_drop",
                    "severity": "critical",
                    "message":  f"On-time rate dropped {round(prev_avg-recent_avg,1)}% in last 3 ticks",
                    "value":    round(recent_avg, 1),
                    "tick":     tick,
                    "time":     time.strftime("%H:%M:%S")
                })

        # ── RULE 2: Distance spike ──
        if len(self.distance_history) >= 8:
            z = self._zscore(avg_dist, list(self.distance_history)[:-1])
            if z > 2.0 and avg_dist > self._mean(self.distance_history) * 1.3:
                detected.append({
                    "type":     "distance_spike",
                    "severity": "warning",
                    "message":  f"Avg distance spiked to {avg_dist}u (z-score: {round(z,2)})",
                    "value":    round(avg_dist, 2),
                    "tick":     tick,
                    "time":     time.strftime("%H:%M:%S")
                })

        # ── RULE 3: Demand surge ──
        if len(self.demand_history) >= 5:
            recent_demand = list(self.demand_history)[-1]
            avg_demand    = self._mean(list(self.demand_history)[:-1])
            if avg_demand > 0 and recent_demand > avg_demand * 2.0:
                detected.append({
                    "type":     "demand_surge",
                    "severity": "warning",
                    "message":  f"Demand surged to {recent_demand} pending orders (2x avg of {round(avg_demand,1)})",
                    "value":    recent_demand,
                    "tick":     tick,
                    "time":     time.strftime("%H:%M:%S")
                })

        # ── RULE 4: Reassignment rate spike ──
        if len(self.breach_history) >= 5:
            recent_r = list(self.breach_history)[-1]
            prev_r   = list(self.breach_history)[-2] if len(self.breach_history) > 1 else 0
            new_breaches = recent_r - prev_r
            if new_breaches >= 3:
                detected.append({
                    "type":     "breach_spike",
                    "severity": "critical",
                    "message":  f"{new_breaches} new SLA breaches in last tick — agent routing issue",
                    "value":    new_breaches,
                    "tick":     tick,
                    "time":     time.strftime("%H:%M:%S")
                })

        # ── RULE 5: All agents overloaded ──
        busy = len([a for a in sim_ref.agents if a.status == "busy"])
        total = len(sim_ref.agents)
        if total > 0 and busy / total >= 1.0 and pending > 20:
            detected.append({
                "type":     "fleet_overload",
                "severity": "critical",
                "message":  f"All {total} agents at full capacity with {pending} orders pending",
                "value":    pending,
                "tick":     tick,
                "time":     time.strftime("%H:%M:%S")
            })

        # ── RULE 6: Low demand — agents idle ──
        idle = total - busy
        if idle > total * 0.7 and pending < 3 and tick > 10:
            detected.append({
                "type":     "low_utilization",
                "severity": "info",
                "message":  f"{idle}/{total} agents idle — consider switching to Rush Hour mode",
                "value":    idle,
                "tick":     tick,
                "time":     time.strftime("%H:%M:%S")
            })

        # store new anomalies
        for a in detected:
            self.anomalies.append(a)
            print(f"[ANOMALY] {a['severity'].upper()}: {a['message']}")

        self.last_check = tick
        return detected

    def get_summary(self):
        recent    = self.anomalies[-20:]
        critical  = [a for a in recent if a["severity"] == "critical"]
        warnings  = [a for a in recent if a["severity"] == "warning"]
        info      = [a for a in recent if a["severity"] == "info"]
        return {
            "total":          len(self.anomalies),
            "recent":         recent[-10:],
            "critical_count": len(critical),
            "warning_count":  len(warnings),
            "info_count":     len(info),
            "last_check":     self.last_check
        }

# ── SINGLETON ─────────────────────────────────────────────────────────

_detector = AnomalyDetector()

def get_detector():
    return _detector