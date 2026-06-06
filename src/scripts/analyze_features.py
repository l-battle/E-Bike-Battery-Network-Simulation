"""Feature-value check: do the engineered features carry signal about outcomes?

Loads a generated dataset and reports, for each target, which features it
correlates with most (Pearson + Spearman). Run AFTER run_pilot.

Run with:  python -m src.scripts.analyze_features [path/to/dataset.csv]
"""
import sys

import pandas as pd

DATASET = sys.argv[1] if len(sys.argv) > 1 else "data/experiments/pilot.csv"

FEATURES = [
    "n_riders", "rider_speed_kmh", "n_lockers", "total_capacity",
    "lockers_per_rider", "capacity_per_rider", "coverage_3min", "coverage_5min",
    "coverage_10min", "mean_demand_to_locker_min", "p90_demand_to_locker_min",
    "unmet_demand_frac", "locker_dispersion",
]
TARGETS = [
    "stranded_per_hour", "failed_swaps_per_hour", "swap_success_rate",
    "trips_per_hour", "locker_utilization", "mean_battery_wh",
]

df = pd.read_csv(DATASET)
print(f"Loaded {len(df)} rows from {DATASET}\n")

# Drop features/targets that don't vary (no signal possible).
features = [c for c in FEATURES if c in df.columns and df[c].std() > 0]
targets = [c for c in TARGETS if c in df.columns and df[c].std() > 0]

dropped_t = [c for c in TARGETS if c in df.columns and df[c].std() == 0]
if dropped_t:
    print(f"(constant targets, skipped: {dropped_t})\n")

print("=== Target ranges ===")
print(df[targets].describe().loc[["mean", "std", "min", "max"]].T, "\n")

for target in targets:
    pear = df[features + [target]].corr(method="pearson")[target].drop(target)
    spear = df[features + [target]].corr(method="spearman")[target].drop(target)

    table = pd.DataFrame({"pearson": pear, "spearman": spear})
    table["abs"] = table["pearson"].abs()
    table = table.sort_values("abs", ascending=False).drop(columns="abs")

    print(f"=== {target}: features by |correlation| ===")
    print(table.head(8).round(3).to_string())
    print()
