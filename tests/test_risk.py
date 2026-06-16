import pytest

from tests.conftest import build_grid_graph
from src.experiments.config import ExperimentConfig
from src.experiments.risk import (
    evaluate_decision, risk_profile, probability_exceeds, probability_below,
    value_at_risk,
)


@pytest.fixture
def base_graph():
    return build_grid_graph()


def small_config(**kw):
    params = dict(
        name="decision", n_riders=4, n_lockers=2,
        locker_csv=None, hotspot_csv=None, ferry_csv=None,
        n_steps=80, warmup_steps=20, seconds_per_step=10,
    )
    params.update(kw)
    return ExperimentConfig(**params)


def test_evaluate_decision_runs_each_condition(base_graph):
    df = evaluate_decision(small_config(), seeds=(0, 1, 2), base_graph=base_graph)
    assert len(df) == 3
    assert "stranded_per_hour" in df.columns
    assert "delivery_success_rate" in df.columns


def test_evaluate_decision_seeds_and_weathers(base_graph):
    df = evaluate_decision(small_config(), seeds=(0, 1),
                           weathers=["clear", "snow"], base_graph=base_graph)
    assert len(df) == 2 * 2          # seeds x weathers


def test_risk_profile_keys_and_order(base_graph):
    df = evaluate_decision(small_config(), seeds=(0, 1, 2, 3), base_graph=base_graph)
    prof = risk_profile(df, "stranded_per_hour")
    assert set(prof) == {"mean", "std", "min", "p10", "p50", "p90", "max"}
    assert prof["min"] <= prof["p50"] <= prof["max"]


def test_probability_exceeds_is_a_probability(base_graph):
    df = evaluate_decision(small_config(), seeds=range(5), base_graph=base_graph)
    p = probability_exceeds(df, "stranded_per_hour", threshold=0.0)
    assert 0.0 <= p <= 1.0


def test_probability_below_complements_exceeds(base_graph):
    df = evaluate_decision(small_config(), seeds=range(5), base_graph=base_graph)
    below = probability_below(df, "stranded_per_hour", threshold=1.0)
    assert 0.0 <= below <= 1.0
    # strictly-below + (>= threshold) accounts for all runs
    at_or_above = float((df["stranded_per_hour"] >= 1.0).mean())
    assert below + at_or_above == pytest.approx(1.0)


def test_value_at_risk_within_range(base_graph):
    df = evaluate_decision(small_config(), seeds=range(5), base_graph=base_graph)
    var = value_at_risk(df, "stranded_per_hour", quantile=0.9)
    assert df["stranded_per_hour"].min() <= var <= df["stranded_per_hour"].max()


def test_delivery_success_rate_bounded(base_graph):
    df = evaluate_decision(small_config(), seeds=(0, 1, 2), base_graph=base_graph)
    assert df["delivery_success_rate"].between(0.0, 1.0).all()
