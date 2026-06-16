import pytest

from tests.conftest import node_lonlat
from src.environment.city_graph import CityGraph


def test_nearest_node_returns_closest(city):
    lon, lat = node_lonlat(8)
    assert city.nearest_node(x=lon, y=lat) == 8

    lon0, lat0 = node_lonlat(0)
    assert city.nearest_node(x=lon0, y=lat0) == 0


def test_distance_to_node_haversine(city):
    # One node directly north of node 0 by 0.001 deg latitude ~ 111 m.
    lon0, lat0 = node_lonlat(0)
    d = city.distance_to_node(0, x=lon0, y=lat0 + 0.001)
    assert d == pytest.approx(111.3, abs=2.0)


def test_distance_to_self_is_zero(city):
    lon0, lat0 = node_lonlat(0)
    assert city.distance_to_node(0, x=lon0, y=lat0) == pytest.approx(0.0, abs=1e-6)


def test_annotate_travel_costs(annotated_city):
    # 100 m edge at 18 km/h (5 m/s) -> 20 s; 0.1 km * 12 Wh/km -> 1.2 Wh.
    tt, bc, is_ferry = annotated_city.edge_cost(0, 1)
    assert tt == pytest.approx(20.0)
    assert bc == pytest.approx(1.2)
    assert is_ferry is False


def test_edge_cost_missing_edge(annotated_city):
    # Nodes 0 and 8 are not directly connected in the grid.
    assert annotated_city.edge_cost(0, 8) == (0.0, 0.0, False)


def test_shortest_path_uses_travel_time(annotated_city):
    # Make the direct hop 0->1 extremely slow; the path should detour around it.
    for data in annotated_city.graph.get_edge_data(0, 1).values():
        data["travel_time"] = 10_000

    path = annotated_city.shortest_path(0, 2)
    consecutive = list(zip(path, path[1:]))
    assert (0, 1) not in consecutive
    assert path[0] == 0 and path[-1] == 2


def test_has_path(city):
    assert city.has_path(0, 8) is True
    city.graph.add_node(999, x=0.0, y=0.0)  # isolated
    assert city.has_path(0, 999) is False


def test_random_reachable_destination(city):
    dest = city.random_reachable_destination(0)
    assert dest in city.graph.nodes
    assert dest != 0


def test_random_reachable_node_pair_distinct(city):
    a, b = city.random_reachable_node_pair()
    assert a != b
    assert city.has_path(a, b)


def test_add_ferry_routes(annotated_city):
    records = [{
        "name": "F", "from_lat": node_lonlat(0)[1], "from_lon": node_lonlat(0)[0],
        "to_lat": node_lonlat(8)[1], "to_lon": node_lonlat(8)[0],
        "crossing_seconds": 210, "wait_seconds": 180,
    }]
    annotated_city.add_ferry_routes(records)

    tt, bc, is_ferry = annotated_city.edge_cost(0, 8)
    assert is_ferry is True
    assert tt == pytest.approx(390.0)       # crossing + wait
    assert bc == 0.0                        # ferries consume no battery
    # Bidirectional
    assert annotated_city.edge_cost(8, 0)[2] is True


def test_add_ferry_routes_is_idempotent(annotated_city):
    records = [{
        "name": "F", "from_lat": node_lonlat(0)[1], "from_lon": node_lonlat(0)[0],
        "to_lat": node_lonlat(8)[1], "to_lon": node_lonlat(8)[0],
        "crossing_seconds": 210, "wait_seconds": 180,
    }]
    annotated_city.add_ferry_routes(records)
    edges_after_first = annotated_city.graph.number_of_edges()
    annotated_city.add_ferry_routes(records)        # again
    assert annotated_city.graph.number_of_edges() == edges_after_first


def test_injected_graph_skips_osm(grid_graph):
    # Constructing with a graph must not hit the network.
    cg = CityGraph(graph=grid_graph)
    assert cg.graph is grid_graph
