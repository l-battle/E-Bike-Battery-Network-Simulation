import random

class HotspotManager:
    def __init__(self, model, hotspots=None, hotspot_probability=0.7, spread=10):
        self.model = model
        self.hotspot_probability = hotspot_probability
        self.spread = spread

        self.hotspots = hotspots or [
            (25, 25),
            (75, 75),
            (50, 30),
        ]

    def get_destination(self):
        if random.random() < self.hotspot_probability:
            hotspot_x, hotspot_y = random.choice(self.hotspots)

            x = random.gauss(hotspot_x, self.spread)
            y = random.gauss(hotspot_y, self.spread)

            x = max(0, min(self.model.width, x))
            y = max(0, min(self.model.height, y))

            return x,y
        
        return (
            random.uniform(0, self.model.width),
            random.uniform(0, self.model.height),
        )