import numpy as np
import random
import json
import os
from collections import defaultdict

# ── Q-TABLE AGENT ─────────────────────────────────────────────────────

class QLearningAgent:
    def __init__(self):
        self.q_table      = defaultdict(lambda: defaultdict(float))
        self.alpha        = 0.1    # learning rate
        self.gamma        = 0.9    # discount factor
        self.epsilon      = 0.3    # exploration rate
        self.epsilon_min  = 0.05
        self.epsilon_decay= 0.995
        self.episodes     = 0
        self.total_reward = 0.0
        self.rewards_log  = []

    # ── STATE ENCODER ──────────────────────────────────────────────────

    def encode_state(self, agent, order, traffic_zones):
        """
        Encode agent-order pair into discrete state bucket.
        State = (distance_bucket, capacity_bucket, priority, deadline_bucket)
        """
        from utils import euclidean_distance, get_traffic_delay

        dist     = euclidean_distance(agent.location, order.location)
        delay    = get_traffic_delay(agent.location, traffic_zones)
        eff_dist = dist * delay

        # discretize into buckets
        dist_bucket     = min(int(eff_dist / 20), 4)      # 0-4
        cap_bucket      = len(agent.current_orders)        # 0-5
        priority        = order.priority                   # 1-3
        deadline_bucket = min(int(order.deadline / 30), 3) # 0-3

        return (dist_bucket, cap_bucket, priority, deadline_bucket)

    # ── ACTION SELECTION ───────────────────────────────────────────────

    def select_action(self, state):
        """Epsilon-greedy action selection. 0=skip, 1=assign."""
        if random.random() < self.epsilon:
            return random.choice([0, 1])
        q_assign = self.q_table[state][1]
        q_skip   = self.q_table[state][0]
        return 1 if q_assign >= q_skip else 0

    # ── LEARNING ───────────────────────────────────────────────────────

    def update(self, state, action, reward, next_state):
        """Q-learning update rule."""
        current_q  = self.q_table[state][action]
        max_next_q = max(self.q_table[next_state][0],
                         self.q_table[next_state][1])
        new_q      = current_q + self.alpha * (
            reward + self.gamma * max_next_q - current_q
        )
        self.q_table[state][action] = new_q
        self.total_reward          += reward
        self.rewards_log.append(reward)

        # decay exploration
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay

    # ── REWARD FUNCTION ────────────────────────────────────────────────

    def compute_reward(self, agent, order, traffic_zones, was_assigned):
        """Compute reward for assign/skip decision."""
        if not was_assigned:
            # skipping a high priority order is bad
            return -order.priority * 2

        from utils import euclidean_distance, get_traffic_delay
        dist     = euclidean_distance(agent.location, order.location)
        delay    = get_traffic_delay(agent.location, traffic_zones)
        est_time = dist * delay * 0.5

        if est_time <= order.deadline:
            # on-time delivery reward — higher for urgent orders
            return 10 + order.priority * 3
        elif est_time <= order.deadline * 1.2:
            # slightly late — small penalty
            return 2
        else:
            # will miss deadline — penalty
            return -8

    # ── SAVE / LOAD ────────────────────────────────────────────────────

    def save(self, path="rl_qtable.json"):
        data = {
            "q_table":      {str(k): dict(v) for k, v in self.q_table.items()},
            "epsilon":      self.epsilon,
            "episodes":     self.episodes,
            "total_reward": self.total_reward
        }
        with open(path, "w") as f:
            json.dump(data, f)
        print(f"[RL] Q-table saved → {path} ({len(self.q_table)} states)")

    def load(self, path="rl_qtable.json"):
        if not os.path.exists(path):
            print("[RL] No saved Q-table found — starting fresh")
            return
        with open(path, "r") as f:
            data = json.load(f)
        for k, v in data["q_table"].items():
            state = tuple(map(int, k.strip("()").split(",")))
            self.q_table[state] = defaultdict(float, {int(a): r for a, r in v.items()})
        self.epsilon      = data.get("epsilon", 0.3)
        self.episodes     = data.get("episodes", 0)
        self.total_reward = data.get("total_reward", 0.0)
        print(f"[RL] Q-table loaded — {len(self.q_table)} states, epsilon={self.epsilon:.3f}")

    def get_stats(self):
        avg_reward = round(
            sum(self.rewards_log[-100:]) / max(len(self.rewards_log[-100:]), 1), 2
        )
        return {
            "states_explored": len(self.q_table),
            "epsilon":         round(self.epsilon, 4),
            "episodes":        self.episodes,
            "total_reward":    round(self.total_reward, 2),
            "avg_reward_100":  avg_reward,
            "is_trained":      len(self.q_table) > 20
        }

# ── RL ASSIGNMENT ENGINE ──────────────────────────────────────────────

def assign_orders_rl(sim, agent: QLearningAgent, verbose=False, training=True):
    """
    RL-based order assignment.
    Uses Q-table to decide assign/skip for each agent-order pair.
    """
    from engine import agent_can_take_order

    pending        = sim.get_pending_orders()
    assigned_count = 0
    skipped_count  = 0

    pending.sort(key=lambda o: (-o.priority, o.deadline))

    for order in pending:
        best_agent = None
        best_score = -999

        for ag in sim.get_available_agents():
            can, reason = agent_can_take_order(ag, order, sim.traffic_zones)
            if not can:
                continue

            state  = agent.encode_state(ag, order, sim.traffic_zones)
            action = agent.select_action(state)

            if action == 1:  # assign
                reward     = agent.compute_reward(ag, order, sim.traffic_zones, True)
                next_state = (0, len(ag.current_orders) + 1,
                              order.priority, min(int(order.deadline / 30), 3))
                if training:
                    agent.update(state, action, reward, next_state)

                if reward > best_score:
                    best_score = reward
                    best_agent = ag
            else:  # skip
                reward = agent.compute_reward(ag, order, sim.traffic_zones, False)
                if training:
                    agent.update(state, action, reward,
                                 agent.encode_state(ag, order, sim.traffic_zones))

        if best_agent:
            order.assigned_agent = best_agent.agent_id
            order.status         = "assigned"
            best_agent.current_orders.append(order.order_id)
            if len(best_agent.current_orders) >= best_agent.capacity:
                best_agent.status = "busy"
            assigned_count += 1
            agent.episodes += 1
            if verbose:
                print(f"[RL] Order {order.order_id} → Agent {best_agent.agent_id} "
                      f"| Score: {best_score:.1f} | ε={agent.epsilon:.3f}")
        else:
            skipped_count += 1
            order.status = "failed"

    return assigned_count, skipped_count

# ── TRAINING RUNNER ───────────────────────────────────────────────────

def train_rl_agent(episodes=50):
    """
    Train RL agent over multiple simulation episodes.
    Returns training history for plotting.
    """
    from simulation import SimulationState
    from realtime import move_agents, detect_and_reassign, inject_new_orders, MetricsTracker

    agent   = QLearningAgent()
    history = []

    print(f"[RL] Starting training — {episodes} episodes")

    for ep in range(episodes):
        sim     = SimulationState()
        metrics = MetricsTracker()
        assign_orders_rl(sim, agent, training=True)

        for tick in range(1, 15):
            move_agents(sim, metrics)
            detect_and_reassign(sim, metrics)
            if tick % 2 == 0:
                inject_new_orders(sim, metrics, tick)
            assign_orders_rl(sim, agent, training=True)

        from engine import get_quality_metrics
        avg_dist, on_time, _ = get_quality_metrics(sim)

        history.append({
            "episode":     ep + 1,
            "on_time":     metrics.get_on_time_rate(),
            "avg_distance": round(avg_dist, 2),
            "epsilon":     round(agent.epsilon, 4),
            "delivered":   metrics.total_delivered
        })

        if (ep + 1) % 10 == 0:
            print(f"[RL] Episode {ep+1}/{episodes} | "
                  f"On-time: {metrics.get_on_time_rate()}% | "
                  f"ε={agent.epsilon:.3f}")

    agent.save()
    print(f"[RL] Training complete — {len(agent.q_table)} states explored")
    return agent, history

# ── SINGLETON ─────────────────────────────────────────────────────────

_rl_agent    = None
_rl_history  = []
_rl_status   = {"status": "untrained", "training": False}

def get_rl_agent():
    global _rl_agent
    if _rl_agent is None:
        _rl_agent = QLearningAgent()
        _rl_agent.load()
    return _rl_agent

def get_rl_status():
    agent = get_rl_agent()
    return {
        **_rl_status,
        **agent.get_stats(),
        "history": _rl_history[-20:]
    }

def start_training(episodes=50):
    import threading
    if _rl_status["training"]:
        return {"status": "already_training"}

    _rl_status["training"] = True
    _rl_status["status"]   = "training"

    def run():
        global _rl_agent, _rl_history
        agent, history  = train_rl_agent(episodes)
        _rl_agent       = agent
        _rl_history     = history
        _rl_status["training"] = False
        _rl_status["status"]   = "trained"
        print(f"[RL] Training complete!")

    threading.Thread(target=run, daemon=True).start()
    return {"status": "started", "episodes": episodes}