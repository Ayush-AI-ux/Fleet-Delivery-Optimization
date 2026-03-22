
import random
import logging
from utils import euclidean_distance, get_traffic_delay
from simulation import SimulationState

# ── LOGGING SETUP ─────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(message)s",
    datefmt="%H:%M:%S"
)
log = logging.getLogger(__name__)

# ── WEIGHT CONSTANTS (patchable by optimizer) ─────────────────────────

W_PROXIMITY = 0.5
W_CAPACITY  = 0.2
W_URGENCY   = 0.2
W_DEADLINE  = 0.1

# ── SCORING FUNCTION ──────────────────────────────────────────────────

def score_agent_for_order(agent, order, traffic_zones):
    """
    Higher score = better match.
    Factors: proximity, available capacity, deadline urgency, traffic delay
    """
    distance = euclidean_distance(agent.location, order.location)
    delay    = get_traffic_delay(agent.location, traffic_zones)

    effective_distance = distance * delay

    if effective_distance == 0:
        proximity_score = 100
    else:
        proximity_score = 1 / effective_distance

    capacity_score = (agent.capacity - len(agent.current_orders)) / agent.capacity
    urgency_score  = order.priority / 3.0
    deadline_score = 1 / max(order.deadline, 1)

    total = (
        W_PROXIMITY * proximity_score +
        W_CAPACITY  * capacity_score  +
        W_URGENCY   * urgency_score   +
        W_DEADLINE  * deadline_score
    )

    return round(total, 6)

# ── CONSTRAINT CHECKER ────────────────────────────────────────────────

def agent_can_take_order(agent, order, traffic_zones):
    """Hard constraints — agent is skipped if any fail."""
    if len(agent.current_orders) >= agent.capacity:
        return False, "capacity full"

    distance = euclidean_distance(agent.location, order.location)
    delay    = get_traffic_delay(agent.location, traffic_zones)
    est_time = distance * delay * 0.5

    if est_time > order.deadline:
        return False, f"cannot reach in time (est {est_time:.1f}s > deadline {order.deadline:.1f}s)"

    return True, "ok"

# ── GREEDY ASSIGNMENT ENGINE ──────────────────────────────────────────

def assign_orders(sim: SimulationState, verbose=True):
    """
    For each pending order, find the best available agent using
    constraint checking + scoring. Assign and log the decision.
    """
    pending        = sim.get_pending_orders()
    assigned_count = 0
    skipped_count  = 0

    pending.sort(key=lambda o: (-o.priority, o.deadline))

    for order in pending:
        best_agent  = None
        best_score  = -1
        best_reason = ""

        for agent in sim.get_available_agents():
            can, reason = agent_can_take_order(agent, order, sim.traffic_zones)
            if not can:
                continue

            score = score_agent_for_order(agent, order, sim.traffic_zones)
            if score > best_score:
                best_score  = score
                best_agent  = agent
                best_reason = reason

        if best_agent:
            order.assigned_agent = best_agent.agent_id
            order.status         = "assigned"
            best_agent.current_orders.append(order.order_id)
            if len(best_agent.current_orders) >= best_agent.capacity:
                best_agent.status = "busy"

            assigned_count += 1

            if verbose:
                dist = euclidean_distance(best_agent.location, order.location)
                log.info(
                    f"ORDER {order.order_id:>3} → AGENT {best_agent.agent_id:>2} | "
                    f"Score: {best_score:.4f} | "
                    f"Dist: {dist:.1f}u | "
                    f"Priority: {order.priority} | "
                    f"Deadline: {order.deadline:.1f}s | "
                    f"Cap used: {len(best_agent.current_orders)}/{best_agent.capacity}"
                )
        else:
            skipped_count += 1
            order.status = "failed"
            if verbose:
                log.warning(f"ORDER {order.order_id:>3} → NO AGENT AVAILABLE")

    return assigned_count, skipped_count

# ── BASELINE RANDOM ASSIGNER ──────────────────────────────────────────

def assign_orders_random(sim: SimulationState):
    """Randomly assigns orders — used as baseline to measure improvement."""
    pending   = sim.get_pending_orders()
    available = sim.get_available_agents()
    assigned  = 0

    for order in pending:
        eligible = [a for a in available if len(a.current_orders) < a.capacity]
        if eligible:
            agent = random.choice(eligible)
            order.assigned_agent = agent.agent_id
            order.status         = "assigned"
            agent.current_orders.append(order.order_id)
            assigned += 1
        else:
            order.status = "failed"

    return assigned

# ── QUALITY METRICS ───────────────────────────────────────────────────

def get_quality_metrics(sim):
    assigned_orders = [o for o in sim.orders if o.status == "assigned"]
    if not assigned_orders:
        return 0, 0, 0

    total_dist   = 0
    deadline_met = 0

    for order in assigned_orders:
        agent = sim.get_agent_by_id(order.assigned_agent)
        if agent:
            dist     = euclidean_distance(agent.location, order.location)
            delay    = get_traffic_delay(agent.location, sim.traffic_zones)
            est_time = dist * delay * 0.5
            total_dist += dist
            if est_time <= order.deadline:
                deadline_met += 1

    avg_dist     = round(total_dist / len(assigned_orders), 2)
    on_time_rate = round((deadline_met / len(assigned_orders)) * 100, 1)
    return avg_dist, on_time_rate, len(assigned_orders)

def print_metrics(sim, assigned, skipped, label="OPTIMIZED"):
    total                = len(sim.orders)
    rate                 = round((assigned / total) * 100, 1)
    avg_dist, on_time, _ = get_quality_metrics(sim)

    print(f"\n{'='*50}")
    print(f"  RESULTS — {label}")
    print(f"{'='*50}")
    print(f"  Total Orders     : {total}")
    print(f"  Assigned         : {assigned}")
    print(f"  Failed/Skipped   : {skipped}")
    print(f"  Assignment Rate  : {rate}%")
    print(f"  Avg Distance     : {avg_dist}u")
    print(f"  On-Time Rate     : {on_time}%")
    print(f"{'='*50}\n")

# ── RUN ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import time

    print("\n>>> RUNNING OPTIMIZED ENGINE...\n")
    sim1           = SimulationState()
    t1             = time.time()
    a1, s1         = assign_orders(sim1, verbose=True)
    t1             = round(time.time() - t1, 4)
    avg_dist1, on_time1, _ = get_quality_metrics(sim1)
    print_metrics(sim1, a1, s1, label="OPTIMIZED")

    print("\n>>> RUNNING RANDOM BASELINE...\n")
    sim2           = SimulationState()
    t2             = time.time()
    a2             = assign_orders_random(sim2)
    t2             = round(time.time() - t2, 4)
    s2             = len(sim2.orders) - a2
    avg_dist2, on_time2, _ = get_quality_metrics(sim2)
    print_metrics(sim2, a2, s2, label="RANDOM BASELINE")

    dist_improvement   = round(((avg_dist2 - avg_dist1) / max(avg_dist2, 1)) * 100, 1)
    ontime_improvement = round(on_time1 - on_time2, 1)

    print(f"{'='*50}")
    print(f"  COMPARISON SUMMARY")
    print(f"{'='*50}")
    print(f"  Avg Distance  → Optimized: {avg_dist1}u  |  Random: {avg_dist2}u")
    print(f"  Distance Improvement : {dist_improvement}% shorter routes")
    print(f"  On-Time Rate  → Optimized: {on_time1}%  |  Random: {on_time2}%")
    print(f"  On-Time Improvement  : +{ontime_improvement}% more on-time deliveries")
    print(f"{'='*50}\n")