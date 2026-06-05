import pytest

from tests.conftest import build_grid_graph
from src.environment.city_graph import CityGraph
from src.simulation.graph_model import GraphBatterySwapModel
from src.agents.graph_rider import GraphRider
from src.agents.graph_locker import GraphLocker
from src.utils.config import (
    BATTERY_CAPACITY_WH, MODE_DELIVERING, MODE_SEEKING_LOCKER, MODE_STRANDED,
)


def riders_of(model):
    return [a for a in model.agents if isinstance(a, GraphRider)]


def lockers_of(model):
    return [a for a in model.agents if isinstance(a, GraphLocker)]


def build_model(weather="clear", n_riders=1, n_lockers=1):
    cg = CityGraph(graph=build_grid_graph())
    return GraphBatterySwapModel(
        city_graph=cg, n_riders=n_riders, n_lockers=n_lockers,
        seconds_per_step=10, weather=weather,
    )


def test_movement_advances_and_drains_battery():
    model = build_model()
    rider = riders_of(model)[0]
    rider.current_node = 0
    rider.route = [0, 1, 2]
    rider.route_index = 0
    rider.time_into_edge = 0.0
    rider.battery_level = 500.0
    rider.mode = MODE_DELIVERING

    rider._advance(20)  # exactly one 100 m edge (20 s at 18 km/h)

    assert rider.current_node == 1
    assert rider.route_index == 1
    assert rider.battery_level == pytest.approx(498.8)  # 500 - 1.2 Wh


def test_zero_battery_strands_rider():
    model = build_model()
    rider = riders_of(model)[0]
    rider.current_node = 0
    rider.route = [0, 1]
    rider.route_index = 0
    rider.time_into_edge = 0.0
    rider.battery_level = 0.5
    rider.mode = MODE_DELIVERING
    failed_before = model.failed_swaps
    stranded_before = model.stranded_count

    rider._advance(20)

    assert rider.battery_level == 0
    assert rider.mode == MODE_STRANDED
    assert model.failed_swaps == failed_before + 1
    assert model.stranded_count == stranded_before + 1


def test_low_battery_reroutes_to_locker():
    model = build_model(n_lockers=2)
    rider = riders_of(model)[0]
    rider.current_node = 0
    rider.route = [0, 1, 2]
    rider.route_index = 0
    rider.battery_level = 50.0          # below 100 Wh threshold
    rider.battery_threshold = 100.0
    rider.mode = MODE_DELIVERING

    rider.step()

    assert rider.mode == MODE_SEEKING_LOCKER
    assert rider.target_locker is not None


def test_try_swap_resets_battery_and_counts():
    model = build_model(n_lockers=1)
    rider = riders_of(model)[0]
    locker = lockers_of(model)[0]
    locker.charged_batteries = 5

    rider.current_node = locker.node_id
    rider.trip_destination_node = (locker.node_id + 1) % 9
    rider.target_locker = locker
    rider.mode = MODE_SEEKING_LOCKER
    rider.battery_level = 80.0
    swaps_before = model.swap_count
    charged_before = locker.charged_batteries

    rider.try_swap()

    assert model.swap_count == swaps_before + 1
    assert locker.charged_batteries == charged_before - 1
    assert locker.depleted_batteries == 1
    assert rider.battery_level == BATTERY_CAPACITY_WH
    assert rider.mode == MODE_DELIVERING
    assert rider.target_locker is None


def test_try_swap_empty_locker_strands():
    model = build_model(n_lockers=1)
    rider = riders_of(model)[0]
    locker = lockers_of(model)[0]
    locker.charged_batteries = 0
    rider.target_locker = locker
    rider.mode = MODE_SEEKING_LOCKER

    rider.try_swap()

    assert rider.mode == MODE_STRANDED


def test_complete_delivery_picks_new_destination():
    model = build_model()
    rider = riders_of(model)[0]
    rider.current_node = 0
    trips_before = model.completed_trips

    rider.complete_delivery()

    assert model.completed_trips == trips_before + 1
    assert rider.trip_destination_node != rider.current_node
    assert rider.mode == MODE_DELIVERING


def test_weather_increases_battery_drain_per_edge():
    def drain_for(weather):
        model = build_model(weather=weather)
        rider = riders_of(model)[0]
        rider.current_node = 0
        rider.route = [0, 1]
        rider.route_index = 0
        rider.time_into_edge = 0.0
        rider.battery_level = 500.0
        rider.mode = MODE_DELIVERING
        rider._advance(1000)  # large budget -> completes the edge fully
        return 500.0 - rider.battery_level

    clear = drain_for("clear")
    snow = drain_for("snow")
    assert snow > clear
    assert snow == pytest.approx(clear * 1.30)  # snow battery_factor
