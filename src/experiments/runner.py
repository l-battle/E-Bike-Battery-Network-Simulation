"""Run simulation experiments: seeded single runs, grids, and sweeps.

Each run returns a flat result row (config fields + normalised steady-state
metrics) suitable as a row of an ML training table.
"""
import json
import random
import itertools
from pathlib import Path

import numpy as np
import pandas as pd

from src.environment.city_graph import CityGraph
from src.simulation.graph_model import GraphBatterySwapModel
from src.experiments.config import ExperimentConfig

RESULTS_DIR = Path("data/experiments")

# Config fields that identify a scenario (everything except the seed).
GROUP_KEYS = [
    "name", "place_name", "locker_csv", "hotspot_csv", "ferry_csv",
    "n_lockers", "n_riders", "weather", "rider_speed_kmh",
    "seconds_per_step", "n_steps", "warmup_steps",
]

METRIC_KEYS = [
    "trips_per_hour", "swaps_per_hour", "failed_swaps_per_hour",
    "stranded_per_hour", "swap_success_rate", "mean_battery_wh",
    "mean_stranded_riders", "locker_utilization",
]


def set_seed(seed):
    random.seed(seed)
    np.random.seed(seed)


def load_base_graph(place_name="Amsterdam, Netherlands"):
    """Download/load the real graph once; reuse a copy per run."""
    return CityGraph(place_name).graph


def run_experiment(config: ExperimentConfig, base_graph=None):
    """Run one experiment and return a result row (config + metrics)."""
    set_seed(config.seed)

    if base_graph is not None:
        # Fresh copy so per-run mutations (ferry edges, cost annotation)
        # never leak between runs.
        city_graph = CityGraph(graph=base_graph.copy())
    else:
        city_graph = CityGraph(config.place_name)

    model = GraphBatterySwapModel(
        city_graph=city_graph,
        n_riders=config.n_riders,
        n_lockers=config.n_lockers,
        locker_csv=config.locker_csv,
        hotspot_csv=config.hotspot_csv,
        ferry_csv=config.ferry_csv,
        weather=config.weather,
        seconds_per_step=config.seconds_per_step,
        rider_speed_kmh=config.rider_speed_kmh,
    )

    for _ in range(config.n_steps):
        model.step()

    return {**config.to_dict(),
            **summarize(model, config.warmup_steps, config.seconds_per_step)}


def summarize(model, warmup_steps, seconds_per_step):
    """Normalised, steady-state metrics over the post-warmup window."""
    history = model.history
    warmup = warmup_steps
    end = history[-1]
    base = history[warmup - 1] if warmup > 0 else None

    def delta(key):
        return end[key] - (base[key] if base else 0)

    window = history[warmup:]
    window_steps = len(window)
    hours = window_steps * seconds_per_step / 3600 if window_steps else 0

    def per_hour(key):
        return delta(key) / hours if hours > 0 else 0.0

    swaps = delta("swap_count")
    failed = delta("failed_swaps")
    completed = delta("completed_trips")
    stranded = delta("stranded_count")
    n_lockers = max(len(model.graph_lockers), 1)

    mean = lambda key: (sum(r[key] for r in window) / len(window)) if window else 0.0

    return {
        "n_lockers_actual": len(model.graph_lockers),
        "has_demand": model.demand is not None,
        "trips_per_hour": per_hour("completed_trips"),
        "swaps_per_hour": per_hour("swap_count"),
        "failed_swaps_per_hour": per_hour("failed_swaps"),
        "stranded_per_hour": per_hour("stranded_count"),
        "swap_success_rate": swaps / (swaps + failed) if (swaps + failed) else 1.0,
        # Robust service level: of all delivery outcomes (completed or
        # stranded), the fraction completed. Defined whenever there is activity,
        # unlike swap_success_rate which is degenerate (=1) with no swaps.
        "delivery_success_rate":
            completed / (completed + stranded) if (completed + stranded) else 1.0,
        "mean_battery_wh": mean("avg_battery"),
        "mean_stranded_riders": mean("stranded_riders"),
        "locker_utilization": per_hour("swap_count") / n_lockers,
    }


def expand_grid(base: ExperimentConfig, grid: dict, seeds):
    """Cartesian product of grid values x seeds, applied onto `base`.

    `grid` maps a config field name to a list of values. Returns a list of
    ExperimentConfig, with names tagged by their varied values + seed.
    """
    keys = list(grid)
    configs = []
    for combo in itertools.product(*(grid[k] for k in keys)):
        overrides = dict(zip(keys, combo))
        tag = "_".join(f"{k}={v}" for k, v in overrides.items())
        for seed in seeds:
            configs.append(
                base.with_overrides(
                    name=f"{base.name}_{tag}" if tag else base.name,
                    seed=seed,
                    **overrides,
                )
            )
    return configs


def run_sweep(configs, base_graph=None, place_name="Amsterdam, Netherlands",
              progress=True):
    """Run many configs, reusing one loaded graph. Returns a list of rows."""
    if base_graph is None:
        base_graph = load_base_graph(place_name)

    rows = []
    for i, cfg in enumerate(configs, 1):
        if progress:
            print(f"[{i}/{len(configs)}] {cfg.name} seed={cfg.seed}")
        rows.append(run_experiment(cfg, base_graph=base_graph))
    return rows


def to_dataframe(rows):
    return pd.DataFrame(rows)


def aggregate(rows, group_keys=None, metric_keys=None):
    """Mean and std of metrics across seeds, grouped by scenario."""
    group_keys = group_keys or GROUP_KEYS
    metric_keys = metric_keys or METRIC_KEYS
    df = to_dataframe(rows)
    present = [k for k in group_keys if k in df.columns]
    return (
        df.groupby(present, dropna=False)[metric_keys]
        .agg(["mean", "std"])
        .reset_index()
    )


def save_results(rows, stem):
    """Write raw per-run rows to JSON and CSV under data/experiments/."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    json_path = RESULTS_DIR / f"{stem}.json"
    csv_path = RESULTS_DIR / f"{stem}.csv"

    with open(json_path, "w") as f:
        json.dump(rows, f, indent=2)
    to_dataframe(rows).to_csv(csv_path, index=False)

    return json_path, csv_path
