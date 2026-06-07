import pandas as pd
from sklearn.model_selection import GroupShuffleSplit
from collections import namedtuple

GROUP_COL = "combo_id"

FEATURES = [
    "n_riders", "rider_speed_kmh", "weather",
    "n_lockers", "lockers_per_rider",
    "coverage_3min", "coverage_5min", "coverage_10min",
    "mean_demand_to_locker_min", "p90_demand_to_locker_min",
    "unmet_demand_frac", "locker_dispersion",
]

TARGETS = [
    "stranded_per_hour", "swap_success_rate", "locker_utilization",
    "trips_per_hour", "swaps_per_hour", "mean_battery_wh",
    "mean_stranded_riders",
]

# what make_dataset hands back
Dataset = namedtuple(
    "Dataset",
    ["X_train", "X_test", "y_train", "y_test", "feature_names", "target_names"],
)

def load_dataset(path):
    df = pd.read_csv(path)
    missing = set(FEATURES + TARGETS + [GROUP_COL]) - set(df.columns)
    if missing:
        raise ValueError(f"Dataset missing columns: {sorted(missing)}")
    return df

def prepare_features(df):
    return pd.get_dummies(df[FEATURES], columns=["weather"])

def prepare_targets(df):
    return df[TARGETS]

def group_split(X, y, groups, test_size=0.2, seed=0):
    gss = GroupShuffleSplit(n_splits=1, test_size=test_size, random_state=seed)
    train_idx, test_idx = next(gss.split(X, y, groups))
    return (
        X.iloc[train_idx], X.iloc[test_idx],
        y.iloc[train_idx], y.iloc[test_idx],
    )

def make_dataset(path, test_size=0.2, seed=0):
    df = load_dataset(path)
    X = prepare_features(df)
    y = prepare_targets(df)
    groups = df[GROUP_COL]

    X_train, X_test, y_train, y_test = group_split(
        X, y, groups, test_size=test_size, seed=seed
    )
    return Dataset(
        X_train, X_test, y_train, y_test,
        feature_names=list(X.columns),
        target_names=TARGETS,
    )