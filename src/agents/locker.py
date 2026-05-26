import mesa
from mesa import Agent

class Locker(mesa.Agent):
    """battery locker"""

    def __init__(self, model, locker_id, charged_batteries = 0):
        super().__init__(model)
        self.locker_id = locker_id
        self.charged_batteries = charged_batteries