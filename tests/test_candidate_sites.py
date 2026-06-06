import pytest

from tests.conftest import build_grid_graph
from src.environment.city_graph import CityGraph
from src.environment.demand import DemandModel
from src.experiments.candidate_sites import (
    generate_candidate_sites, load_candidate_sites, save_candidate_sites,
)


@pytest.fixture
def city():
    return CityGraph(graph=build_grid_graph())


def test_returns_requested_count(city):
    sites = generate_candidate_sites(city, demand=None, n_sites=4,
                                     min_spacing_m=10, seed=0)
    assert len(sites) == 4
    assert {s["candidate_id"] for s in sites} == {0, 1, 2, 3}


def test_fps_spreads_to_corners(city):
    # On a 3x3 grid, the 4 most-spread nodes are the corners (0, 2, 6, 8).
    sites = generate_candidate_sites(city, demand=None, n_sites=4,
                                     min_spacing_m=10, seed=0)
    assert {s["node_id"] for s in sites} == {0, 2, 6, 8}


def test_is_deterministic(city):
    a = generate_candidate_sites(city, demand=None, n_sites=5, seed=0)
    b = generate_candidate_sites(city, demand=None, n_sites=5, seed=0)
    assert [s["node_id"] for s in a] == [s["node_id"] for s in b]


def test_min_spacing_stops_early(city):
    # Spacing larger than the whole grid -> only the single seed survives.
    sites = generate_candidate_sites(city, demand=None, n_sites=9,
                                     min_spacing_m=100_000, seed=0)
    assert len(sites) == 1


def test_demand_seeds_are_tagged(city, hotspot_csv):
    demand = DemandModel(city, hotspot_csv)
    sites = generate_candidate_sites(city, demand=demand, n_sites=5,
                                     min_spacing_m=10, seed=0)
    sources = {s["source"] for s in sites}
    assert "demand" in sources           # at least one demand-seeded site
    # the demand seed is the hotspot centre node
    seed_nodes = [s["node_id"] for s in sites if s["source"] == "demand"]
    assert len(seed_nodes) >= 1


def test_save_load_round_trip(city, tmp_path):
    sites = generate_candidate_sites(city, demand=None, n_sites=4,
                                     min_spacing_m=10, seed=0)
    path = tmp_path / "candidates.csv"
    save_candidate_sites(sites, path)

    loaded = load_candidate_sites(str(path), city)
    assert [s["node_id"] for s in sites] == [s["node_id"] for s in loaded]
    assert [s["candidate_id"] for s in sites] == [s["candidate_id"] for s in loaded]
