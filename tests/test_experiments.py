import pytest

from tests.conftest import build_grid_graph
from src.experiments.config import ExperimentConfig
from src.experiments.runner import (
    run_experiment, expand_grid, aggregate, METRIC_KEYS,
)


@pytest.fixture
def base_graph():
    return build_grid_graph()


def small_config(**kw):
    params = dict(
        name="t", n_riders=3, n_lockers=2,
        locker_csv=None, hotspot_csv=None, ferry_csv=None,
        n_steps=60, warmup_steps=10, seconds_per_step=10,
    )
    params.update(kw)
    return ExperimentConfig(**params)


def test_run_experiment_returns_config_and_metrics(base_graph):
    row = run_experiment(small_config(), base_graph=base_graph)
    # config fields present
    assert row["n_riders"] == 3
    assert row["weather"] == "clear"
    # all metrics present and finite
    for key in METRIC_KEYS:
        assert key in row
        assert row[key] == row[key]  # not NaN


def test_same_seed_is_deterministic(base_graph):
    cfg = small_config(seed=42)
    r1 = run_experiment(cfg, base_graph=base_graph)
    r2 = run_experiment(cfg, base_graph=base_graph)
    for key in METRIC_KEYS:
        assert r1[key] == r2[key]


def test_base_graph_not_mutated_by_ferry(base_graph, ferry_csv):
    before_edges = base_graph.number_of_edges()
    cfg = small_config(ferry_csv=ferry_csv)
    run_experiment(cfg, base_graph=base_graph)
    # The run copies the graph; the shared base must be untouched.
    assert base_graph.number_of_edges() == before_edges
    assert not any(d.get("is_ferry") for _, _, d in base_graph.edges(data=True))


def test_expand_grid_counts():
    base = small_config()
    grid = {"n_riders": [5, 10], "weather": ["clear", "rain"]}
    seeds = [0, 1, 2]
    configs = expand_grid(base, grid, seeds)
    assert len(configs) == 2 * 2 * 3
    # seeds applied
    assert {c.seed for c in configs} == {0, 1, 2}
    # overrides applied
    assert {c.n_riders for c in configs} == {5, 10}


def test_aggregate_groups_over_seeds(base_graph):
    base = small_config()
    configs = expand_grid(base, {"n_riders": [3, 5]}, seeds=[0, 1])
    rows = [run_experiment(c, base_graph=base_graph) for c in configs]
    summary = aggregate(rows)
    # 2 scenarios (n_riders 3 and 5), each aggregated over 2 seeds
    assert len(summary) == 2
