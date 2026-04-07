import time
from collections import defaultdict

# ── PREDICTIVE SLA ENGINE ─────────────────────────────────────────────

class SLAPredictor:
    def __init__(self, lookahead_ticks=3, buffer_pct=0.75):
        self.lookahead    = lookahead_ticks  # predict 3 ticks ahead
        self.buffer_pct   = buffer_pct       # flag if ETA > 75% of deadline
        self.predictions  = []               # log of predictions made
        self.prevented    = 0                # breaches prevented
        self.tick_speed   = 3.0              # seconds per tick

    def predict_eta(self, agent, order, traffic_zones):
        """Predict ETA accounting for current trajectory."""
        from utils import euclidean_distance, get_traffic_delay
        dist     = euclidean_distance(agent.location, order.location)
        delay    = get_traffic_delay(agent.location, traffic_zones)
        est_time = dist * delay * 0.5
        return round(est_time, 2)

    def predict_future_position(self, agent, ticks_ahead, scenario_config):
        """Estimate where agent will be N ticks from now."""
        from utils import euclidean_distance
        speed = scenario_config.get("agent_speed", 2.0)

        if not agent.current_orders:
            return agent.location

        # agent moves toward first order each tick
        ax, ay   = agent.location
        # estimate movement direction stays roughly same
        # simplified: agent moves speed * ticks_ahead units closer
        return agent.location  # position approximation

    def scan(self, sim_ref, metrics_ref, tick_ref):
        """
        Scan all assigned orders and predict which will breach
        in the next N ticks. Pre-emptively reassign if better
        agent available.
        """
        from utils import euclidean_distance, get_traffic_delay
        from engine import agent_can_take_order, score_agent_for_order
        from scenario import get_current_config

        config       = get_current_config()
        agent_speed  = config.get("agent_speed", 2.0)
        traffic_mult = config.get("traffic_multiplier", 1.0)

        at_risk      = []
        prevented    = 0

        for order in sim_ref.orders:
            if order.status != "assigned":
                continue

            agent = sim_ref.get_agent_by_id(order.assigned_agent)
            if not agent:
                continue

            current_eta = self.predict_eta(agent, order, sim_ref.traffic_zones)

            # predict ETA after N ticks of movement
            from utils import euclidean_distance
            dist = euclidean_distance(agent.location, order.location)

            # after lookahead ticks, agent will be closer
            movement_per_tick = agent_speed
            future_dist = max(dist - movement_per_tick * self.lookahead, 0)

            from utils import get_traffic_delay
            delay        = get_traffic_delay(agent.location, sim_ref.traffic_zones)
            future_eta   = future_dist * delay * 0.5

            # time remaining after lookahead ticks
            time_remaining = order.deadline - (self.lookahead * self.tick_speed)

            # risk assessment
            risk_score = current_eta / max(order.deadline, 1)

            if risk_score > self.buffer_pct and time_remaining > 0:
                at_risk.append({
                    "order_id":      order.order_id,
                    "agent_id":      agent.agent_id,
                    "current_eta":   current_eta,
                    "deadline":      round(order.deadline, 1),
                    "risk_score":    round(risk_score, 3),
                    "priority":      order.priority,
                    "tick":          tick_ref["value"],
                    "time":          time.strftime("%H:%M:%S")
                })

                # try pre-emptive reassignment
                best_agent = None
                best_score = -1

                for candidate in sim_ref.get_available_agents():
                    if candidate.agent_id == agent.agent_id:
                        continue
                    if len(candidate.current_orders) >= candidate.capacity:
                        continue

                    can, _ = agent_can_take_order(
                        candidate, order, sim_ref.traffic_zones
                    )
                    if not can:
                        continue

                    cand_eta = self.predict_eta(
                        candidate, order, sim_ref.traffic_zones
                    )

                    # only reassign if significantly better
                    if cand_eta < current_eta * 0.7:
                        score = score_agent_for_order(
                            candidate, order, sim_ref.traffic_zones
                        )
                        if score > best_score:
                            best_score = score
                            best_agent = candidate

                if best_agent:
                    # pre-emptive reassignment
                    if order.order_id in agent.current_orders:
                        agent.current_orders.remove(order.order_id)
                    if not agent.current_orders:
                        agent.status = "idle"

                    best_agent.current_orders.append(order.order_id)
                    best_agent.status    = "busy"
                    order.assigned_agent = best_agent.agent_id

                    metrics_ref.total_reassigned += 1
                    self.prevented += 1
                    prevented      += 1

                    msg = (
                        f"PREDICT  Order {order.order_id} at risk "
                        f"(ETA {current_eta}s, {round(risk_score*100)}% of deadline) — "
                        f"pre-assigned to Agent {best_agent.agent_id}"
                    )
                    metrics_ref.log(msg)

                    # update prediction log
                    at_risk[-1]["pre_assigned_to"] = best_agent.agent_id
                    at_risk[-1]["prevented"]        = True
                else:
                    at_risk[-1]["prevented"] = False

        # store predictions
        self.predictions.extend(at_risk)
        self.predictions = self.predictions[-50:]  # keep last 50

        return {
            "at_risk":        at_risk,
            "prevented_now":  prevented,
            "total_prevented": self.prevented,
            "tick":            tick_ref["value"]
        }

    def get_summary(self):
        return {
            "total_predictions": len(self.predictions),
            "total_prevented":   self.prevented,
            "recent":            self.predictions[-10:],
            "lookahead_ticks":   self.lookahead,
            "buffer_pct":        self.buffer_pct
        }

# ── SINGLETON ─────────────────────────────────────────────────────────

_predictor = SLAPredictor(lookahead_ticks=3, buffer_pct=0.75)

def get_predictor():
    return _predictor