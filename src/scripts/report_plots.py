"""Generate surrogate-quality plots for the beta report (fast; no graph needed).

Run with:  python -m src.scripts.report_plots
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")

from src.ai.dataset import make_dataset
from src.ai.surrogate import train_surrogate
from src.visualization.ai_plots import (
    plot_parity, plot_metric_bars, plot_feature_importance,
)

DATASET = "data/experiments/dataset_v1.csv"
OUT = Path("data/exports/report")
TARGETS = [
    "mean_stranded_riders", "stranded_per_hour", "swap_success_rate",
    "locker_utilization", "trips_per_hour", "swaps_per_hour", "mean_battery_wh",
]

OUT.mkdir(parents=True, exist_ok=True)
ds = make_dataset(DATASET, test_size=0.25, seed=0)
surrogate, metrics = train_surrogate(ds)
y_pred = surrogate.predict(ds.X_test)

plot_parity(ds.y_test, y_pred, TARGETS).savefig(OUT / "surrogate_parity.png", dpi=90)
plot_metric_bars(metrics).savefig(OUT / "surrogate_accuracy.png", dpi=90)
plot_feature_importance(surrogate, ds.X_test, ds.y_test,
                        "mean_stranded_riders").savefig(
    OUT / "feature_importance.png", dpi=90)

print(f"Saved report plots to {OUT}/")
for t, m in metrics.items():
    print(f"  {t:24s} R2={m['r2']:.2f}  Spearman={m['spearman']:.2f}")
