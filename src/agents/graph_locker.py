import warnings

from mesa import Agent
from src.utils.config import DEFAULT_CHARGE_SECONDS, DEFAULT_LOCKER_CAPACITY


class GraphLocker(Agent):
    def __init__(
        self,
        model,
        locker_id,
        node_id,
        charged_batteries=5,
        capacity=DEFAULT_LOCKER_CAPACITY,
        charge_seconds=DEFAULT_CHARGE_SECONDS,
    ):
        super().__init__(model)

        self.locker_id = locker_id
        self.node_id = node_id
        self.capacity = capacity

        if charged_batteries > capacity:
            warnings.warn(
                f"Locker {locker_id} starts with {charged_batteries} charged "
                f"batteries but capacity is {capacity}; clamping to capacity.",
                stacklevel=2,
            )
            charged_batteries = capacity

        self.charged_batteries = charged_batteries
        self.depleted_batteries = 0

        # Each depleted battery carries the seconds remaining until charged.
        self.charge_seconds = charge_seconds
        self.charging_queue = []

    @property
    def total_batteries(self):
        return self.charged_batteries + self.depleted_batteries

    def add_depleted_battery(self):
        """Accept a rider's spent battery to charge (one swapped in for one out,
        so the total never exceeds capacity)."""
        if self.total_batteries >= self.capacity:
            return

        self.depleted_batteries += 1
        self.charging_queue.append(self.charge_seconds)

    def step(self):
        # Advance charging by the simulated time elapsed this step.
        elapsed = self.model.seconds_per_step
        updated_queue = []

        for remaining_seconds in self.charging_queue:
            remaining_seconds -= elapsed

            if remaining_seconds <= 0:
                self.depleted_batteries -= 1
                self.charged_batteries += 1
            else:
                updated_queue.append(remaining_seconds)

        self.charging_queue = updated_queue
