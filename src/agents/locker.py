import mesa
from mesa import Agent

class Locker(mesa.Agent):
    """battery locker"""

    def __init__(self, model, locker_id, x, y, charged_batteries = 0):
        super().__init__(model)
        self.locker_id = locker_id
        self.x = x
        self.y = y
        self.charged_batteries = charged_batteries