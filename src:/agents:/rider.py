from mesa import Agent

class Rider(Agent):
    """A rider """

    def __init__(self, model, rider_id, battery_level=100):
        super().__init__(model)
        self.rider_id = rider_id
        self.battery_level = battery_level

    def step(self):
        self.battery_level -= 5

        if self.battery_level <= 20:
            self.try_swap()

    def try_swap(self):
        lockers = [
            agent for agent in self.model.agents
            if agent.__class__.__name__ == "Locker"
        ]

        available_lockers = [
            locker for locker in lockers 
            if  locker.charged_batteries > 0
        ]

        if available_lockers:
            locker = available_lockers[0]
            locker.charged_batteries -= 1
            self.battery_level = 100
            print(f"Rider {self.rider_id} swapped battery at locked {locker.locker_id}.")
        else:
            print(f"Rider {self.rider_id} could not find a charged battery.")