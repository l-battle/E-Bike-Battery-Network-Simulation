import pytest

from src.environment.weather import Weather
from src.environment.demand import DemandModel, load_hotspot_records
from src.environment.locker_data import load_locker_records
from src.environment.ferry_data import load_ferry_records
from src.utils.config import WEATHER_PRESETS


# ---- Weather ----

@pytest.mark.parametrize("condition", list(WEATHER_PRESETS))
def test_weather_presets_match_config(condition):
    w = Weather(condition)
    preset = WEATHER_PRESETS[condition]
    assert w.travel_time_factor == preset["travel_time_factor"]
    assert w.battery_factor == preset["battery_factor"]


def test_weather_clear_is_neutral():
    w = Weather("clear")
    assert w.travel_time_factor == 1.0 and w.battery_factor == 1.0


def test_weather_invalid_raises():
    with pytest.raises(ValueError):
        Weather("typhoon")


# ---- Loaders ----

def test_load_locker_records(locker_csv):
    records = load_locker_records(locker_csv)
    assert len(records) == 2
    r = records[0]
    assert isinstance(r["locker_id"], int)
    assert isinstance(r["lat"], float) and isinstance(r["lon"], float)
    assert r["capacity"] == 10


def test_load_ferry_records(ferry_csv):
    records = load_ferry_records(ferry_csv)
    assert len(records) == 1
    assert records[0]["crossing_seconds"] == 210
    assert records[0]["wait_seconds"] == 180


def test_load_hotspot_records(hotspot_csv):
    records = load_hotspot_records(hotspot_csv)
    assert len(records) == 1
    assert records[0]["weight"] == 5.0
    assert records[0]["radius_m"] == 500


# ---- DemandModel ----

def test_demand_model_builds_zone(city, hotspot_csv):
    dm = DemandModel(city, hotspot_csv)
    assert dm.is_active
    assert len(dm.hotspots) == 1
    # radius 500 m covers the whole ~222 m grid -> all 9 nodes in the zone.
    assert len(dm.hotspots[0]["zone_nodes"]) == city.graph.number_of_nodes()


def test_demand_sample_returns_graph_node(city, hotspot_csv):
    dm = DemandModel(city, hotspot_csv)
    for _ in range(20):
        assert dm.sample_node() in city.graph.nodes


def test_demand_sample_respects_exclude(city, hotspot_csv):
    dm = DemandModel(city, hotspot_csv)
    for _ in range(20):
        assert dm.sample_node(exclude=4) != 4


def test_demand_empty_zone_warns_and_skips(city, tmp_path):
    p = tmp_path / "far.csv"
    p.write_text(
        "hotspot_id,name,lat,lon,weight,radius_m\n"
        "0,Nowhere,0.0,0.0,5,50\n"   # far from the grid, tiny radius
    )
    with pytest.warns(UserWarning):
        dm = DemandModel(city, str(p))
    assert not dm.is_active
    with pytest.raises(ValueError):
        dm.sample_node()
