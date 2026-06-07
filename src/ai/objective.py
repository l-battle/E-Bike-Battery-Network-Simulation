DIRECTIONS = {
    "stranded_per_hour": "min",
    "swap_success_rate": "max",
    "locker_utilization": "max",
}

class Objective:
    def __init__(self, weights=None, directions=DIRECTIONS):
        self.directions = directions
        self.weights = weights or {t: 1.0 for t in directions}
        self.ranges = None 

    def fit(self, y):
        """y: a targets DataFrame (e.g. dataset.y_train) to learn normalisation
        ranges from."""
        self.ranges = {t: (y[t].min(), y[t].max()) for t in self.directions}
        return self
    
    def _normalize(self, target, value):
        lo, hi = self.ranges[target]
        if hi == lo:
            return 0.0
        z = (value - lo) / (hi - lo)
        z = min(1.0, max(0.0, z))
        if self.directions[target] == "min":
            z = 1.0 - z
        return z
    
    def score(self, predicted):
        """predicted: dict/Series with the objective target values
        (e.g. a row of surrogate.predict())."""
        if self.ranges is None:
            raise ValueError("Objective not fitted; call fit() first.")
        total_w = sum(self.weights[t] for t in self.directions)
        s = sum(
            self.weights[t] * self._normalize(t, predicted[t])
            for t in self.directions
        )
        return s / total_w