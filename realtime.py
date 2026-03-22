import time
import random
import threading
from simulation import SimulationState, Order
from engine import assign_orders, get_quality_metrics
from utils import euclidean_distance, get_traffic_delay

# ── CONFIG ────────────────────────────────────────────────────────────

TICK_INTERVAL    = 3
NEW_ORDER_RATE   = 3
AGENT_SPEED      = 2.0
SLA_BUFFER       = 5.0
SIMULATION_TICKS = 20

# ── METRICS TRACKER ───────────────────────────────────────────────────

class MetricsTracker:
    def __init__(self):
        self.total_assigned      = 0
        self.total_reassigned    = 0
        self.total_delivered     = 0
        self.total_failed        = 0
        self.on_time_deliveries  = 0
        self.decision_logs       = []

    def log(self, message):
        timestamp = time.strftime("%H:%M:%S")
        entry     = f"[{timestamp}] {message}"
        self.decision_logs.append(entry)
        print(entry)

    def get_on_time_rate(self):
        total = self.total_delivered + self.total_failed
        if total == 0:
            return 0.0
        return round((self.on_time_deliveries / total) * 100, 1)

# ── AGENT MOVEMENT ────────────────────────────────────────────────────

def move_agents(sim, metrics):
    from scenario import get_current_config
    config = get_current_config()
    speed  = config["agent_speed"]

    for agent in sim.agents:
        if not agent.current_orders:
            agent.status = "idle"
            continue

        target_order = sim.get_order_by_id(agent.current_orders[0])
        if not target_order:
            continue

        ax, ay = agent.location
        ox, oy = target_order.location
        dist   = euclidean_distance(agent.location, target_order.location)

        if dist <= speed:
            agent.location = target_order.location
            agent.current_orders.pop(0)
            target_order.status = "delivered"
            metrics.total_delivered += 1
            metrics.on_time_deliveries += 1
            metrics.log(f"DELIVERED  Order {target_order.order_id} by Agent {agent.agent_id}")
        else:
            ratio          = speed / dist
            new_x          = round(ax + ratio * (ox - ax), 2)
            new_y          = round(ay + ratio * (oy - ay), 2)
            agent.location = (new_x, new_y)# ── SLA BREACH DETECTOR ───────────────────────────────────────────────

def detect_and_reassign(sim, metrics):
    """
    Check every assigned order. If estimated arrival > deadline,
    try to reassign to a better available agent.
    """
    for order in sim.orders:
        if order.status != "assigned":
            continue

        current_agent = sim.get_agent_by_id(order.assigned_agent)
        if not current_agent:
            continue

        dist     = euclidean_distance(current_agent.location, order.location)
        delay    = get_traffic_delay(current_agent.location, sim.traffic_zones)
        est_time = dist * delay * 0.5

        if est_time > (order.deadline - SLA_BUFFER):
            # SLA breach predicted — find better agent
            metrics.log(
                f"SLA BREACH  Order {order.order_id} | "
                f"Agent {current_agent.agent_id} ETA {est_time:.1f}s > "
                f"Deadline {order.deadline:.1f}s — searching reassignment..."
            )

            best_agent = None
            best_score = -1

            for agent in sim.get_available_agents():
                if agent.agent_id == current_agent.agent_id:
                    continue
                if len(agent.current_orders) >= agent.capacity:
                    continue

                new_dist     = euclidean_distance(agent.location, order.location)
                new_delay    = get_traffic_delay(agent.location, sim.traffic_zones)
                new_est_time = new_dist * new_delay * 0.5

                if new_est_time < order.deadline:
                    score = 1 / max(new_dist, 0.1)
                    if score > best_score:
                        best_score = score
                        best_agent = agent

            if best_agent:
                # remove from current agent
                if order.order_id in current_agent.current_orders:
                    current_agent.current_orders.remove(order.order_id)
                if not current_agent.current_orders:
                    current_agent.status = "idle"

                # assign to new agent
                best_agent.current_orders.append(order.order_id)
                best_agent.status       = "busy"
                order.assigned_agent    = best_agent.agent_id

                metrics.total_reassigned += 1
                metrics.log(
                    f"REASSIGNED  Order {order.order_id} → "
                    f"Agent {best_agent.agent_id} "
                    f"(ETA now {euclidean_distance(best_agent.location, order.location)*0.5:.1f}s)"
                )
            else:
                metrics.log(
                    f"FAILED      Order {order.order_id} — no agent can meet deadline"
                )
                order.status = "failed"
                metrics.total_failed += 1
                if order.order_id in current_agent.current_orders:
                    current_agent.current_orders.remove(order.order_id)

# ── NEW ORDER INJECTOR ────────────────────────────────────────────────

def inject_new_orders(sim, metrics, tick):
    from scenario import get_current_config
    config = get_current_config()
    rate   = config["new_order_rate"]
    start_id = 1000 + tick * 20

    for i in range(rate):
        new_order = Order(
            order_id = start_id + i,
            location = (random.randint(0, 100), random.randint(0, 100)),
            priority = random.randint(1, 3),
            deadline = random.uniform(30, 90)
        )
        sim.orders.append(new_order)

    metrics.log(f"INJECTED    {rate} new orders at tick {tick} [{config['name']}]")
# ── TICK SUMMARY ──────────────────────────────────────────────────────

def print_tick_summary(sim, metrics, tick):
    pending   = len([o for o in sim.orders if o.status == "pending"])
    assigned  = len([o for o in sim.orders if o.status == "assigned"])
    delivered = len([o for o in sim.orders if o.status == "delivered"])
    failed    = len([o for o in sim.orders if o.status == "failed"])
    idle      = len([a for a in sim.agents if a.status == "idle"])

    print(f"\n{'─'*55}")
    print(f"  TICK {tick:>2} | Orders: {len(sim.orders)} total")
    print(f"  Pending:{pending:>4}  Assigned:{assigned:>4}  "
          f"Delivered:{delivered:>4}  Failed:{failed:>3}")
    print(f"  Agents Idle: {idle}/{len(sim.agents)} | "
          f"Reassignments: {metrics.total_reassigned} | "
          f"On-Time Rate: {metrics.get_on_time_rate()}%")
    print(f"{'─'*55}\n")

# ── MAIN SIMULATION LOOP ──────────────────────────────────────────────

def run_simulation():
    print("\n" + "="*55)
    print("   REAL-TIME FLEET AI DECISION ENGINE")
    print("="*55)

    sim     = SimulationState()
    metrics = MetricsTracker()

    # initial assignment
    print("\n>>> Initial assignment pass...\n")
    assigned, skipped = assign_orders(sim, verbose=False)
    metrics.total_assigned += assigned
    metrics.log(f"INIT  Assigned {assigned} orders, {skipped} pending")

    # main loop
    for tick in range(1, SIMULATION_TICKS + 1):
        print(f"\n{'='*55}")
        print(f"  TICK {tick} — sleeping {TICK_INTERVAL}s...")
        print(f"{'='*55}")
        time.sleep(TICK_INTERVAL)

        sim.tick = tick

        # step 1: move agents
        move_agents(sim, metrics)

        # step 2: detect SLA breaches and reassign
        detect_and_reassign(sim, metrics)

        # step 3: inject new orders every 2 ticks
        if tick % 2 == 0:
            inject_new_orders(sim, metrics, tick)

        # step 4: assign any new pending orders
        new_assigned, _ = assign_orders(sim, verbose=False)
        if new_assigned:
            metrics.total_assigned += new_assigned
            metrics.log(f"ASSIGNED  {new_assigned} newly injected orders")

        # step 5: print tick summary
        print_tick_summary(sim, metrics, tick)

    # final report
    print("\n" + "="*55)
    print("   FINAL SIMULATION REPORT")
    print("="*55)
    print(f"  Total Ticks        : {SIMULATION_TICKS}")
    print(f"  Total Orders       : {len(sim.orders)}")
    print(f"  Total Assigned     : {metrics.total_assigned}")
    print(f"  Total Delivered    : {metrics.total_delivered}")
    print(f"  Total Reassigned   : {metrics.total_reassigned}")
    print(f"  Total Failed       : {metrics.total_failed}")
    print(f"  On-Time Rate       : {metrics.get_on_time_rate()}%")
    print("="*55 + "\n")

# ── ENTRY POINT ───────────────────────────────────────────────────────

if __name__ == "__main__":
    run_simulation()