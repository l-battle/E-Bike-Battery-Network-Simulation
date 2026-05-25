from mesa import Model
from agents.rider import Rider
from agents.locker import Locker

class BatterySwapModel(Model):
    def __init__(self, n_riders = 5, n_lockers = 3):
        super().__init()

        for i in range(n_lockers):
            locker = Locker(self, locker_id = i, charged_batteries = 3)
            self.agents.add(locker)

        for i in range(n_riders):
            rider = Rider(self, rider_id = i, battery_level = 100)
            self.agents.add(rider)

    def step(self):
        self.agents.shuffle_do("step")
        