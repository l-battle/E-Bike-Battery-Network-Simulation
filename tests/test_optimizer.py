import pandas as pd
import pytest

from src.environment.demand import DemandModel
from src.experiments.candidate_sites import generate_candidate_sites
from src.experiments.features import compute_features
from src.ai.dataset import prepare_features
from src.ai.objective import Objective
from src.ai.optimizer import greedy_optimize

SCENARIO = {"n_riders": 10, "rider_speed_kmh": 18, "weather": "clear"}
OBJ_TARGETS = ["stranded_per_hour", "swap_success_rate", "locker_utilization"]

# Objective normalisation reference (spans each metric's range).
OBJ_Y = pd.DataFrame({
    "stranded_per_hour":  [0, 5, 10],
    "swap_success_rate":  [0.0, 0.5, 1.0],
    "locker_utilization": [0.0, 0.5, 1.0],
})


# ---- stub surrogates (deterministic, so greedy is testable) ----

class MoreLockersBetter:
    target_names = OBJ_TARGETS

    def predict(self, X):
        n = X.iloc[0]["n_lockers"]
        return pd.DataFrame([{
            "stranded_per_hour": 10 - n,            # more lockers -> fewer
            "swap_success_rate": min(1.0, 0.2 * n),
            "locker_utilization": 0.5,
        }])


class ConstantScore:
    target_names = OBJ_TARGETS

    def predict(self, X):
        return pd.DataFrame([{
            "stranded_per_hour": 5,
            "swap_success_rate": 0.5,
            "locker_utilization": 0.5,
        }])


class CoverageDriven:
    target_names = OBJ_TARGETS

    def predict(self, X):
        cov = X.iloc[0]["coverage_5min"]
        return pd.DataFrame([{
            "stranded_per_hour": 10 * (1 - cov),
            "swap_success_rate": cov,
            "locker_utilization": 0.5,
        }])


# ---- fixtures ----

@pytest.fixture
def demand(annotated_city, hotspot_csv):
    return DemandModel(annotated_city, hotspot_csv)


@pytest.fixture
def candidates(annotated_city, demand):
    return generate_candidate_sites(annotated_city, demand=demand,
                                    n_sites=6, min_spacing_m=10, seed=0)


@pytest.fixture
def feature_names(annotated_city, demand):
    sample_node = list(annotated_city.graph.nodes)[0]
    feats = compute_features(annotated_city, demand, [sample_node], SCENARIO)
    return list(prepare_features(pd.DataFrame([feats])).columns)


def _run(surrogate, candidates, feature_names, annotated_city, demand, budget=3):
    return greedy_optimize(
        candidate_sites=candidates, scenario=SCENARIO, surrogate=surrogate,
        objective=Objective().fit(OBJ_Y), feature_names=feature_names,
        city_graph=annotated_city, demand=demand, budget=budget,
    )


# ---- tests ----

def test_fills_budget_when_more_is_better(candidates, feature_names,
                                          annotated_city, demand):
    chosen, _ = _run(MoreLockersBetter(), candidates, feature_names,
                     annotated_city, demand, budget=3)
    assert len(chosen) == 3


def test_stops_immediately_when_flat(candidates, feature_names,
                                     annotated_city, demand):
    chosen, history = _run(ConstantScore(), candidates, feature_names,
                           annotated_city, demand, budget=3)
    assert chosen == []
    assert len(history) == 1            # only the empty baseline


def test_chosen_are_valid_candidates(candidates, feature_names,
                                     annotated_city, demand):
    chosen, _ = _run(MoreLockersBetter(), candidates, feature_names,
                     annotated_city, demand, budget=4)
    candidate_nodes = {c["node_id"] for c in candidates}
    assert set(chosen) <= candidate_nodes
    assert len(set(chosen)) == len(chosen)          # no duplicates


def test_history_tracks_scores(candidates, feature_names,
                               annotated_city, demand):
    chosen, history = _run(MoreLockersBetter(), candidates, feature_names,
                           annotated_city, demand, budget=3)
    assert len(history) == len(chosen) + 1
    scores = [h["score"] for h in history]
    assert scores == sorted(scores)                 # non-decreasing


def test_coverage_driven_picks_lockers(candidates, feature_names,
                                       annotated_city, demand):
    # Score improves with coverage -> greedy should add at least one locker,
    # which exercises the real feature pipeline (compute_features -> model row).
    chosen, _ = _run(CoverageDriven(), candidates, feature_names,
                     annotated_city, demand, budget=3)
    assert len(chosen) >= 1


def test_empty_candidates_returns_empty(feature_names, annotated_city, demand):
    chosen, history = greedy_optimize(
        candidate_sites=[], scenario=SCENARIO, surrogate=MoreLockersBetter(),
        objective=Objective().fit(OBJ_Y), feature_names=feature_names,
        city_graph=annotated_city, demand=demand, budget=3,
    )
    assert chosen == []
