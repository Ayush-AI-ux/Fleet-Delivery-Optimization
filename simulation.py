
import random
from dataclasses import dataclass, field
from typing import List, Optional
from utils import euclidean_distance, get_traffic_delay

# ── DATA STRUCTURES ───────────────────────────────────────────────────

@dataclass
class Order:
    order_id:       int
    location:       tuple
    priority:       int           # 1=low, 2=medium, 3=high
    deadline:       float         # seconds from now
    assigned_agent: Optional[int] = None
    status:         str = "pending"  # pending / assigned / delivered / failed

@dataclass
class Agent:
    agent_id:       int
    location:       tuple
    capacity:       int
    current_orders: List[int] = field(default_factory=list)
    status:         str = "idle"  # idle / busy

# ── FACTORY FUNCTIONS ─────────────────────────────────────────────────

def create_agents(n=20):
    agents = []
    for i in range(n):
        agents.append(Agent(
            agent_id=i,
            location=(random.randint(0, 100), random.randint(0, 100)),
            capacity=random.randint(2, 5)
        ))
    return agents

def create_orders(n=100):
    orders = []
    for i in range(n):
        orders.append(Order(
            order_id=i,
            location=(random.randint(0, 100), random.randint(0, 100)),
            priority=random.randint(1, 3),
            deadline=random.uniform(30, 120)
        ))
    return orders

# ── SIMULATION STATE ──────────────────────────────────────────────────

class SimulationState:
    def __init__(self):
        from cities import get_current_city
        random.seed(42)
        city = get_current_city()

        self.agents = create_agents(city["agents"])
        self.orders = create_orders(city["orders"])

        # convert city traffic zones to (x, y, radius, multiplier) format
        self.traffic_zones = [
            (zx, zy, radius, multiplier)
            for zx, zy, radius, _, multiplier in city["traffic_zones"]
        ]
        self.tick = 0

    def get_agent_by_id(self, agent_id):
        return next((a for a in self.agents if a.agent_id == agent_id), None)

    def get_order_by_id(self, order_id):
        return next((o for o in self.orders if o.order_id == order_id), None)

    def get_pending_orders(self):
        return [o for o in self.orders if o.status == "pending"]

    def get_available_agents(self):
        return [a for a in self.agents if len(a.current_orders) < a.capacity]

    def summary(self):
        from cities import get_current_city
        city = get_current_city()
        print(f"\n{'='*45}")
        print(f"  SIMULATION STATE — {city['name']} — Tick {self.tick}")
        print(f"{'='*45}")
        print(f"  Total Agents     : {len(self.agents)}")
        print(f"  Total Orders     : {len(self.orders)}")
        print(f"  Pending Orders   : {len(self.get_pending_orders())}")
        print(f"  Available Agents : {len(self.get_available_agents())}")
        print(f"  Traffic Zones    : {len(self.traffic_zones)}")
        print(f"{'='*45}")
        print(f"\n  Sample Agent → ID:{self.agents[0].agent_id} "
              f"Loc:{self.agents[0].location} Cap:{self.agents[0].capacity}")
        print(f"  Sample Order → ID:{self.orders[0].order_id} "
              f"Loc:{self.orders[0].location} Priority:{self.orders[0].priority} "
              f"Deadline:{self.orders[0].deadline:.1f}s")

        d     = euclidean_distance((0, 0), (3, 4))
        delay = get_traffic_delay((25, 25), self.traffic_zones)
        print(f"\n  Distance test    : {d:.2f}  (expected 5.00)")
        print(f"  Traffic zones    : {len(self.traffic_zones)}")
        print(f"{'='*45}\n")

# ── RUN ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    sim = SimulationState()
    sim.summary()