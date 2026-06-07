import pandas as pd
import joblib
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.multioutput import MultiOutputRegressor
from sklearn.metrics import r2_score, mean_absolute_error
from scipy.stats import spearmanr

def train_surrogate(dataset, random_state=0, **gbm_params):
    """Train + evaluate from a Dataset (what make_dataset returns)."""
    surrogate = Surrogate(random_state=random_state, **gbm_params)
    surrogate.fit(dataset.X_train, dataset.y_train)
    metrics = surrogate.evaluate(dataset.X_test, dataset.y_test)
    return surrogate, metrics

class Surrogate():
    def __init__(self, random_state=0, **gbm_params):
        base = HistGradientBoostingRegressor(random_state=random_state, **gbm_params)
        self.model = MultiOutputRegressor(base)
        self.target_names = None

    def fit(self, X, y):
        self.target_names = list(y.columns)
        self.model.fit(X, y)
        return self
    
    def predict(self, X):
        preds = self.model.predict(X)
        return pd.DataFrame(preds, columns=self.target_names, index=X.index)
    
    def evaluate(self, X_test, y_test):
        preds = self.predict(X_test)
        results = {}
        for target in self.target_names:
            actual = y_test[target]
            predicted = preds[target]
            results[target] = {"r2": r2_score(actual, predicted),
                               "mae": mean_absolute_error(actual, predicted),
                               "spearman": spearmanr(actual, predicted).statistic,
                               }
            
        return results
    
    def save(self, path):
        joblib.dump({"model": self.model, "target_names": self.target_names}, path)

    @classmethod
    def load(cls, path):
        blob = joblib.load(path)
        obj = cls()
        obj.model = blob["model"]
        obj.target_names = blob["target_names"]
        return obj