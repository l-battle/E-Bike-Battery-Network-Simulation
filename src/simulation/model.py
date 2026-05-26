from mesa import Model
from src.agents.rider import Rider
from src. agents.locker import Locker
import random

class BatterySwapModel(Model):
    def __init__(self, n_riders = 5, n_lockers = 3, width=100, height=100):
        super().__init__()

        self.width = width
        self.height = height

        #sim metrics
        self.history = []
        self.current_step = 0
        self.swap_count = 0
        self.failed_swaps = 0 

        #temp: lockers at fixed positions 

        locker_positions = [
            (20, 20),
            (50, 50),
            (80, 80)
        ]

        for i in range(n_lockers):
            x, y = locker_positions[i]
            locker = Locker(self, locker_id=i, x=x, y=y, charged_batteries=3, charge_time=10)
            self.agents.add(locker)

        for i in range(n_riders):
            rider = Rider(self, rider_id = i, x=random.uniform(0, width), y=random.uniform(0, height), battery_level=100)
            self.agents.add(rider)

    def step(self):
        self.agents.shuffle_do("step")
        self.current_step += 1
        self.record_history()

    def record_history(self):
        locker_charged_states = {
            f"locker_{agent.locker_id}_charged": agent.charged_batteries
            for agent in self.agents
            if isinstance(agent, Locker)
        }

        locker_depleted_states = {
            f"locker_{agent.locker_id}_depleted": agent.depleted_batteries
            for agent in self.agents
            if isinstance(agent, Locker)
        }


        self.history.append({
            "step": self.current_step,
            "successful_swaps": self.swap_count,
            "failed_swaps": self.failed_swaps,
            "total_charged_batteries": sum(locker_charged_states.values()),
            "total_depleted_batteries": sum(locker_depleted_states.values()),
            **locker_charged_states,
            **locker_depleted_states
        })
