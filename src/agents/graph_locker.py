from mesa import Agent
from src.utils.config import DEFAULT_CHARGE_TIME

class GraphLocker(Agent):
    def __init__(
        self,
        model,
        locker_id,
        node_id,
        charged_batteries=5,
        charge_time=DEFAULT_CHARGE_TIME,
    ):
        super().__init__(model)

        self.locker_id = locker_id
        self.node_id = node_id

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