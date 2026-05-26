from mesa import Model
from src.agents.rider import Rider
from src. agents.locker import Locker

class BatterySwapModel(Model):
    def __init__(self, n_riders = 5, n_lockers = 3):
        super().__init__()

        #sim metrics
        self.history = []
        self.current_step = 0
        self.successful_swaps = 0
        self.failed_swaps = 0
        self.total_battery_depletion = 0
        self.total_distance_travelled = 0
        self.total_energy_consumed = 0

        for i in range(n_lockers):
            locker = Locker(self, locker_id = i, charged_batteries = 3)
            self.agents.add(locker)

        for i in range(n_riders):
            rider = Rider(self, rider_id = i, battery_level = 100)
            self.agents.add(rider)

    def step(self):
        self.agents.shuffle_do("step")
        self.current_step += 1

        locker_states = {
            f"locker_{agent.locker_id}_charged": agent.charged_batteries
            for agent in self.agents
            if isinstance(agent, Locker)
        }

        self.history.append({
            "step": self.current_step,
            "successful_swaps": self.successful_swaps,
            "failed_swaps": self.failed_swaps,
            "total_charged_batteries": sum(locker_states.values()),
            **locker_states
        })
