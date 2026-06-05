"""Example experiment sweep: fleet size x weather, replicated over seeds.

Loads the Amsterdam graph once and reuses it across all runs. Saves raw
per-run rows (ML-ready) and prints an aggregated summary.

Run with:  python -m src.scripts.run_sweep
"""
from src.experiments.config import ExperimentConfig
from src.experiments.runner import (
    expand_grid, run_sweep, aggregate, save_results,
)

# Shorter runs keep the sweep quick; lengthen for real data generation.
base = ExperimentConfig(name="fleet_weather", n_steps=1500, warmup_steps=300)

grid = {
    "n_riders": [10, 20, 30],
    "weather": ["clear", "rain", "snow"],
}
seeds = [0, 1, 2]

configs = expand_grid(base, grid, seeds)
print(f"Running {len(configs)} runs "
      f"({len(configs)//len(seeds)} scenarios x {len(seeds)} seeds)...")

rows = run_sweep(configs)

json_path, csv_path = save_results(rows, stem="fleet_weather")
print(f"\nSaved raw rows to:\n  {json_path}\n  {csv_path}\n")

summary = aggregate(rows)
print("Aggregated (mean over seeds):")
print(
    summary[[
        ("n_riders", ""), ("weather", ""),
        ("trips_per_hour", "mean"), ("stranded_per_hour", "mean"),
        ("swap_success_rate", "mean"), ("mean_battery_wh", "mean"),
    ]].to_string(index=False)
)
