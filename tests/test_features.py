import pytest

from tests.conftest import build_grid_graph
from src.environment.city_graph import CityGraph
from src.environment.demand import DemandModel
from src.experiments.features import compute_features

SCENARIO = {"n_riders": 10, "rider_speed_kmh": 18, "weather": "clear"}

EXPECTED_KEYS = {
    "n_riders", "rider_speed_kmh", "weather",
    "n_lockers", "total_capacity", "lockers_per_rider", "capacity_per_rider",
    "coverage_3min", "coverage_5min", "coverage_10min",
    "mean_demand_to_locker_min", "p90_demand_to_locker_min", "unmet_demand_frac",
    "locker_dispersion",
}


@pytest.fixture
def annotated_city():
    cg = CityGraph(graph=build_grid_graph())
    cg.annotate_travel_costs(speed_kmh=18, consumption_wh_per_km=12)
    return cg


@pytest.fixture
def demand(annotated_city, hotspot_csv):
    return DemandModel(annotated_city, hotspot_csv)


def test_schema(annotated_city, demand):
    f = compute_features(annotated_city, demand, [0, 4], SCENARIO)
    assert set(f) == EXPECTED_KEYS


def test_requires_annotation(demand):
    raw = CityGraph(graph=build_grid_graph())  # not annotated
    with pytest.raises(ValueError):
        compute_features(raw, demand, [0], SCENARIO)


def test_empty_layout(annotated_city, demand):
    f = compute_features(annotated_city, demand, [], SCENARIO)
    assert f["coverage_5min"] == 0.0
    assert f["unmet_demand_frac"] == 1.0
    assert f["locker_dispersion"] == 0.0


def test_full_layout_covers_everything(annotated_city, demand):
    f = compute_features(annotated_city, demand, list(range(9)), SCENARIO)
    assert f["coverage_10min"] == 1.0
    assert f["unmet_demand_frac"] == 0.0
    assert f["mean_demand_to_locker_min"] == pytest.approx(0.0, abs=1e-6)


def test_more_lockers_never_increases_mean_distance(annotated_city, demand):
    one = compute_features(annotated_city, demand, [0], SCENARIO)
    three = compute_features(annotated_city, demand, [0, 4, 8], SCENARIO)
    assert three["mean_demand_to_locker_min"] <= one["mean_demand_to_locker_min"]


def test_central_locker_beats_corner(annotated_city, demand):
    # Demand peaks at the centre (node 4); a central locker is closer on average.
    center = compute_features(annotated_city, demand, [4], SCENARIO)
    corner = compute_features(annotated_city, demand, [0], SCENARIO)
    assert center["mean_demand_to_locker_min"] < corner["mean_demand_to_locker_min"]


def test_dispersion_spread_vs_clustered(annotated_city, demand):
    spread = compute_features(annotated_city, demand, [0, 8], SCENARIO)      # corners
    clustered = compute_features(annotated_city, demand, [0, 1], SCENARIO)   # adjacent
    assert spread["locker_dispersion"] > clustered["locker_dispersion"]


def test_supply_ratios(annotated_city, demand):
    f = compute_features(annotated_city, demand, [0, 4], SCENARIO)
    assert f["n_lockers"] == 2
    assert f["lockers_per_rider"] == pytest.approx(0.2)   # 2 / 10
