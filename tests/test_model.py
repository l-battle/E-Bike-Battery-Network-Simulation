import pytest

from tests.conftest import build_grid_graph
from src.environment.city_graph import CityGraph
from src.simulation.graph_model import GraphBatterySwapModel
from src.agents.graph_rider import GraphRider
from src.utils.config import BATTERY_CAPACITY_WH, WEATHER_PRESETS


def build(**kwargs):
    cg = CityGraph(graph=build_grid_graph())
    params = dict(city_graph=cg, n_riders=3, n_lockers=2, seconds_per_step=10)
    params.update(kwargs)
    return GraphBatterySwapModel(**params)


def riders_of(model):
    return [a for a in model.agents if isinstance(a, GraphRider)]


def test_model_builds_and_steps():
    model = build()
    for _ in range(50):
        model.step()
    assert len(model.history) == 50


def test_history_has_expected_keys():
    model = build()
    model.step()
    row = model.history[0]
    for key in [
        "step", "elapsed_minutes", "weather", "swap_count", "failed_swaps",
        "completed_trips", "stranded_count", "avg_battery", "active_riders",
        "seeking_riders", "stranded_riders", "total_charged_batteries",
        "total_depleted_batteries",
    ]:
        assert key in row


def test_counters_are_monotonic_non_decreasing():
    model = build()
    prev = {"swap_count": 0, "failed_swaps": 0, "completed_trips": 0}
    for _ in range(80):
        model.step()
        row = model.history[-1]
        for k in prev:
            assert row[k] >= prev[k]
            prev[k] = row[k]


def test_battery_stays_within_bounds():
    model = build(n_riders=5)
    for _ in range(100):
        model.step()
        for rider in riders_of(model):
            assert 0 <= rider.battery_level <= BATTERY_CAPACITY_WH


def test_locker_capacity_invariant_holds():
    model = build()
    for _ in range(150):
        model.step()
        for locker in model.graph_lockers:
            assert locker.total_batteries <= locker.capacity


def test_rider_modes_partition_fleet():
    model = build(n_riders=4)
    for _ in range(60):
        model.step()
        row = model.history[-1]
        total = row["active_riders"] + row["seeking_riders"] + row["stranded_riders"]
        assert total == 4


@pytest.mark.parametrize("weather", list(WEATHER_PRESETS))
def test_runs_under_each_weather(weather):
    model = build(weather=weather)
    for _ in range(30):
        model.step()
    assert model.history[-1]["weather"] == weather


def test_runs_with_ferry_and_demand(locker_csv, hotspot_csv, ferry_csv):
    cg = CityGraph(graph=build_grid_graph())
    model = GraphBatterySwapModel(
        city_graph=cg, n_riders=4, seconds_per_step=10,
        locker_csv=locker_csv, hotspot_csv=hotspot_csv, ferry_csv=ferry_csv,
    )
    assert model.demand is not None and model.demand.is_active
    assert len(model.graph_lockers) == 2
    for _ in range(40):
        model.step()
    assert len(model.history) == 40


def test_nearest_available_locker_skips_empty():
    model = build(n_lockers=2)
    for locker in model.graph_lockers:
        locker.charged_batteries = 0
    assert model.nearest_available_locker(0) is None

    model.graph_lockers[0].charged_batteries = 3
    assert model.nearest_available_locker(0) is model.graph_lockers[0]


@pytest.mark.parametrize("seed_riders", [1, 2, 5, 8])
def test_robust_across_fleet_sizes(seed_riders):
    model = build(n_riders=seed_riders)
    for _ in range(40):
        model.step()
    assert len(riders_of(model)) == seed_riders


def test_no_demand_falls_back_to_random():
    model = build()  # no hotspot_csv
    assert model.demand is None
    for _ in range(20):
        model.step()
    assert len(model.history) == 20
