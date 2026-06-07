import pandas as pd
import pytest

from src.ai.dataset import (
    make_dataset, load_dataset, FEATURES, TARGETS, GROUP_COL,
)


def _tiny_csv(tmp_path, n_combos=6, seeds=(0, 1)):
    """A small dataset: n_combos scenarios x seeds, alternating weather."""
    rows = []
    for combo in range(n_combos):
        for seed in seeds:
            row = {c: 1.0 for c in FEATURES + TARGETS}
            row["weather"] = "clear" if combo % 2 == 0 else "rain"
            row[GROUP_COL] = combo
            row["seed"] = seed
            # a couple of excluded columns that must not leak into X
            row["has_demand"] = True
            row["n_lockers_actual"] = 3
            rows.append(row)
    path = tmp_path / "tiny.csv"
    pd.DataFrame(rows).to_csv(path, index=False)
    return str(path)


def test_no_group_leakage(tmp_path):
    path = _tiny_csv(tmp_path)
    df = load_dataset(path)
    ds = make_dataset(path, test_size=0.5, seed=0)

    train_combos = set(df.loc[ds.X_train.index, GROUP_COL])
    test_combos = set(df.loc[ds.X_test.index, GROUP_COL])
    assert train_combos.isdisjoint(test_combos)        # the headline guarantee


def test_weather_is_one_hot_encoded(tmp_path):
    ds = make_dataset(_tiny_csv(tmp_path), seed=0)
    assert "weather" not in ds.feature_names
    assert "weather_clear" in ds.feature_names
    assert "weather_rain" in ds.feature_names


def test_excluded_columns_absent_from_features(tmp_path):
    ds = make_dataset(_tiny_csv(tmp_path), seed=0)
    for col in ["seed", GROUP_COL, "has_demand", "n_lockers_actual"]:
        assert col not in ds.feature_names


def test_targets_present(tmp_path):
    ds = make_dataset(_tiny_csv(tmp_path), seed=0)
    assert set(ds.target_names) == set(TARGETS)
    assert list(ds.y_train.columns) == TARGETS


def test_lengths_align(tmp_path):
    ds = make_dataset(_tiny_csv(tmp_path), seed=0)
    assert len(ds.X_train) == len(ds.y_train)
    assert len(ds.X_test) == len(ds.y_test)
    assert len(ds.X_train) + len(ds.X_test) == 12   # 6 combos x 2 seeds


def test_split_is_deterministic(tmp_path):
    path = _tiny_csv(tmp_path)
    a = make_dataset(path, seed=0)
    b = make_dataset(path, seed=0)
    assert list(a.X_train.index) == list(b.X_train.index)


def test_missing_column_raises(tmp_path):
    df = pd.DataFrame({"n_riders": [1, 2]})   # nowhere near complete
    path = tmp_path / "bad.csv"
    df.to_csv(path, index=False)
    with pytest.raises(ValueError):
        load_dataset(str(path))
