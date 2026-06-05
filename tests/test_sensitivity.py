import pytest

from tests.conftest import build_grid_graph
from src.experiments.config import ExperimentConfig
from src.experiments.sensitivity import (
    run_sensitivity, sensitivity_table, impact_ranking,
)


@pytest.fixture
def base_graph():
    return build_grid_graph()


def small_base():
    return ExperimentConfig(
        name="t", n_riders=3, n_lockers=2,
        locker_csv=None, hotspot_csv=None, ferry_csv=None,
        n_steps=60, warmup_steps=10, seconds_per_step=10,
    )


def test_run_sensitivity_tags_rows(base_graph):
    rows = run_sensitivity(
        small_base(),
        sweeps={"n_riders": {"values": [2, 4]}},
        seeds=[0, 1],
        base_graph=base_graph,
        progress=False,
    )
    assert len(rows) == 2 * 2  # 2 values x 2 seeds
    assert all(r["swept_param"] == "n_riders" for r in rows)
    assert {r["swept_value"] for r in rows} == {2, 4}
    # the swept value actually applied
    assert {r["n_riders"] for r in rows} == {2, 4}


def test_sweep_overrides_applied(base_graph):
    rows = run_sensitivity(
        small_base(),
        sweeps={"n_lockers": {"values": [1, 3], "overrides": {"locker_csv": None}}},
        seeds=[0],
        base_graph=base_graph,
        progress=False,
    )
    assert all(r["locker_csv"] is None for r in rows)
    assert {r["n_lockers"] for r in rows} == {1, 3}


def test_sensitivity_table_shape(base_graph):
    rows = run_sensitivity(
        small_base(),
        sweeps={"n_riders": {"values": [2, 4, 6]}},
        seeds=[0, 1],
        base_graph=base_graph,
        progress=False,
    )
    table = sensitivity_table(rows, ["trips_per_hour", "stranded_per_hour"])
    assert len(table) == 3  # one row per swept value


def test_impact_ranking_returns_sorted(base_graph):
    rows = run_sensitivity(
        small_base(),
        sweeps={
            "n_riders": {"values": [2, 6]},
            "weather": {"values": ["clear", "snow"]},
        },
        seeds=[0],
        base_graph=base_graph,
        progress=False,
    )
    ranking = impact_ranking(rows, "trips_per_hour")
    params = [p for p, _ in ranking]
    spreads = [s for _, s in ranking]
    assert set(params) == {"n_riders", "weather"}
    assert spreads == sorted(spreads, reverse=True)  # descending
