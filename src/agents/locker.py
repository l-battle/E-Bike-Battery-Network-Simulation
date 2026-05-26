import mesa
from mesa import Agent

class Locker(mesa.Agent):
    """battery locker"""

    def __init__(self, model, locker_id, x, y, charged_batteries = 5, charge_time=10):
        super().__init__(model)
        self.locker_id = locker_id
        self.x = x
        self.y = y

        self.charged_batteries = charged_batteries
        self.depleted_batteries = 0

        self.charge_time = charge_time
        self.charging_queue = []

    def add_depleted_battery(self):
        self.depleted_batteries += 1
        self.charging_queue.append(self.charge_time)

    def step(self):
        updated_queue = []

        for remaining_time in self.charging_queue:
            remaining_time -= 1

            if remaining_time <= 0:
                self.depleted_batteries -= 1
                self.charged_batteries += 1
            else:
                updated_queue.append(remaining_time)

        self.charging_queue = updated_queue

