"""Train the surrogate on a generated dataset and report per-target accuracy.

Run with:  python -m src.scripts.train_surrogate [path/to/dataset.csv]
"""
import sys

from src.ai.dataset import make_dataset
from src.ai.surrogate import train_surrogate

DATASET = sys.argv[1] if len(sys.argv) > 1 else "data/experiments/pilot.csv"

ds = make_dataset(DATASET, test_size=0.25, seed=0)
print(f"Train rows: {len(ds.X_train)}  Test rows: {len(ds.X_test)}  "
      f"Features: {len(ds.feature_names)}\n")

surrogate, metrics = train_surrogate(ds)

print(f"{'target':24s} {'R2':>7s} {'MAE':>10s} {'Spearman':>9s}")
for target, m in metrics.items():
    print(f"{target:24s} {m['r2']:7.3f} {m['mae']:10.3f} {m['spearman']:9.3f}")

surrogate.save("data/experiments/surrogate_pilot.joblib")
print("\nSaved surrogate -> data/experiments/surrogate_pilot.joblib")
