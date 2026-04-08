import threading
import time
from simulation import SimulationState
from engine import assign_orders, get_quality_metrics
from realtime import move_agents, detect_and_reassign, inject_new_orders, MetricsTracker
from cities import CITIES

# ── FLEET INSTANCE ────────────────────────────────────────────────────

class FleetInstance:
    def __init__(self, city_key):
        self.city_key  = city_key
        self.city      = CITIES[city_key]
        self.running   = False
        self.tick      = 0
        self.thread    = None

        # create isolated simulation for this city
        self._init_sim()

    def _init_sim(self):
        from cities import set_city, get_current_city
        # temporarily switch city context for this instance
        original_key = get_current_city()["name"]

        # patch city for this fleet
        from simulation import SimulationState as SS
        import random

        class CitySimState(SS):
            def __init__(self_, city_cfg):
                random.seed(hash(city_cfg["name"]) % 1000)
                from simulation import create_agents, create_orders
                self_.agents = create_agents(city_cfg["agents"])
                self_.orders = create_orders(city_cfg["orders"])
                self_.traffic_zones = [
                    (zx, zy, radius, multiplier)
                    for zx, zy, radius, _, multiplier
                    in city_cfg["traffic_zones"]
                ]
                self_.tick = 0

        self.sim     = CitySimState(self.city)
        self.metrics = MetricsTracker()
        assigned, _  = assign_orders(self.sim, verbose=False)
        self.metrics.total_assigned = assigned

    def get_snapshot(self):
        try:
            avg_dist, on_time, _ = get_quality_metrics(self.sim)
        except:
            avg_dist, on_time = 0, 0

        BASELINE = 52.51
        dist_saved = max(BASELINE - avg_dist, 0)
        cost_saved = round(dist_saved * 12 * self.metrics.total_delivered)

        return {
            "city_key":       self.city_key,
            "city_name":      self.city["name"],
            "city_emoji":     self.city["emoji"],
            "tick":           self.tick,
            "running":        self.running,
            "total_orders":   len(self.sim.orders),
            "delivered":      self.metrics.total_delivered,
            "failed":         self.metrics.total_failed,
            "reassigned":     self.metrics.total_reassigned,
            "on_time_rate":   self.metrics.get_on_time_rate(),
            "avg_distance":   round(avg_dist, 2),
            "agents_busy":    len([a for a in self.sim.agents if a.status == "busy"]),
            "agents_idle":    len([a for a in self.sim.agents if a.status == "idle"]),
            "cost_saved":     cost_saved,
            "dist_saved_pct": round((dist_saved / max(BASELINE, 1)) * 100, 1),
            "total_agents":   len(self.sim.agents),
        }

    def _loop(self):
        while self.running:
            time.sleep(3)
            self.tick += 1
            try:
                move_agents(self.sim, self.metrics)
                detect_and_reassign(self.sim, self.metrics)
                if self.tick % 2 == 0:
                    inject_new_orders(self.sim, self.metrics, self.tick)
                new_assigned, _ = assign_orders(self.sim, verbose=False)
                if new_assigned:
                    self.metrics.total_assigned += new_assigned
            except Exception as e:
                print(f"[FLEET:{self.city_key}] Error tick {self.tick}: {e}")

    def start(self):
        if self.running:
            return
        self.running = True
        self.thread  = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()
        print(f"[FLEET] Started {self.city['name']} fleet")

    def stop(self):
        self.running = False
        print(f"[FLEET] Stopped {self.city['name']} fleet")

    def reset(self):
        self.stop()
        time.sleep(0.5)
        self._init_sim()
        self.tick = 0
        self.start()

# ── MULTI FLEET MANAGER ───────────────────────────────────────────────

class MultiFleetManager:
    def __init__(self):
        self.fleets  = {}
        self.enabled = False

    def start_fleet(self, city_key):
        if city_key not in self.fleets:
            self.fleets[city_key] = FleetInstance(city_key)
        self.fleets[city_key].start()
        self.enabled = True
        return {"status": "started", "city": city_key}

    def stop_fleet(self, city_key):
        if city_key in self.fleets:
            self.fleets[city_key].stop()
        return {"status": "stopped", "city": city_key}

    def start_all(self, city_keys=["bangalore", "delhi", "mumbai"]):
        for key in city_keys:
            self.start_fleet(key)
        return {"status": "all_started", "cities": city_keys}

    def stop_all(self):
        for fleet in self.fleets.values():
            fleet.stop()
        self.enabled = False
        return {"status": "all_stopped"}

    def reset_fleet(self, city_key):
        if city_key in self.fleets:
            self.fleets[city_key].reset()
        return {"status": "reset", "city": city_key}

    def get_all_snapshots(self):
        return {
            "enabled":  self.enabled,
            "fleets":   [f.get_snapshot() for f in self.fleets.values()],
            "rankings": self._get_rankings()
        }

    def _get_rankings(self):
        snapshots = [f.get_snapshot() for f in self.fleets.values()]
        if not snapshots:
            return {}

        def best(key, reverse=True):
            valid = [s for s in snapshots if s[key] > 0]
            if not valid:
                return None
            return sorted(valid, key=lambda x: x[key], reverse=reverse)[0]["city_name"]

        return {
            "best_on_time":    best("on_time_rate"),
            "best_efficiency": best("dist_saved_pct"),
            "most_delivered":  best("delivered"),
            "lowest_failures": best("failed", reverse=False),
        }

# ── SINGLETON ─────────────────────────────────────────────────────────

_manager = MultiFleetManager()

def get_manager():
    return _manager