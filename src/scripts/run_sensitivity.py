"""One-at-a-time sensitivity analysis over the key parameters.

Validates that the simulator responds sensibly to each parameter and ranks
their impact. Saves raw rows + figures.

Run with:  python -m src.scripts.run_sensitivity
"""
from pathlib import Path

import matplotlib.pyplot as plt

from src.experiments.config import ExperimentConfig
from src.experiments.runner import save_results
from src.experiments.sensitivity import run_sensitivity, impact_ranking
from src.visualization.sensitivity_plots import (
    plot_parameter_response, plot_tornado,
)

EXPORT_DIR = Path("data/exports/sensitivity")

base = ExperimentConfig(name="sa", n_steps=1500, warmup_steps=300)

# n_lockers only matters with random placement (no fixed CSV layout).
sweeps = {
    "n_riders": {"values": [10, 20, 30, 40, 50]},
    "n_lockers": {"values": [3, 5, 8, 12], "overrides": {"locker_csv": None}},
    "weather": {"values": ["clear", "rain", "wind", "snow", "heat"]},
    "rider_speed_kmh": {"values": [12, 15, 18, 22]},
}
seeds = [0, 1]

METRICS = ["trips_per_hour", "stranded_per_hour",
           "swap_success_rate", "mean_battery_wh"]
TORNADO_METRIC = "stranded_per_hour"

print("Running sensitivity analysis...")
rows = run_sensitivity(base, sweeps, seeds)
save_results(rows, stem="sensitivity")

print("\nImpact ranking (by range of stranded_per_hour):")
for param, spread in impact_ranking(rows, TORNADO_METRIC):
    print(f"  {param:16s} {spread:.2f}")

EXPORT_DIR.mkdir(parents=True, exist_ok=True)
for param in sweeps:
    fig = plot_parameter_response(rows, param, METRICS)
    fig.savefig(EXPORT_DIR / f"response_{param}.png", dpi=90)
fig = plot_tornado(rows, TORNADO_METRIC)
fig.savefig(EXPORT_DIR / "tornado.png", dpi=90)
print(f"\nSaved figures to {EXPORT_DIR}/")

plt.show()
