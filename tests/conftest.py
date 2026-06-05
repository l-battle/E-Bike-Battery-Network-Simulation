"""Shared test fixtures.

Tests run against a tiny synthetic city graph instead of the real Amsterdam
network, so they are fast, deterministic, and need no network access.
"""
import networkx as nx
import pytest
from mesa import Model

from src.environment.city_graph import CityGraph
from src.simulation.graph_model import GraphBatterySwapModel

# Grid geometry constants (so tests can reference exact node coordinates).
GRID_N = 3
LON0 = 4.90
LAT0 = 52.37
SPACING = 0.001          # ~78-111 m between adjacent nodes
EDGE_LENGTH = 100.0      # metres, for every grid edge


def build_grid_graph(n=GRID_N, lon0=LON0, lat0=LAT0, spacing=SPACING,
                     length=EDGE_LENGTH):
    """An n x n grid as a strongly connected MultiDiGraph with x/y/length,
    mimicking the shape of an OSMnx graph."""
    g = nx.MultiDiGraph()
    for r in range(n):
        for c in range(n):
            g.add_node(r * n + c, x=lon0 + c * spacing, y=lat0 + r * spacing)

    def link(a, b):
        g.add_edge(a, b, length=length)
        g.add_edge(b, a, length=length)

    for r in range(n):
        for c in range(n):
            node = r * n + c
            if c + 1 < n:
                link(node, r * n + (c + 1))
            if r + 1 < n:
                link(node, (r + 1) * n + c)
    return g


def node_lonlat(node, n=GRID_N, lon0=LON0, lat0=LAT0, spacing=SPACING):
    r, c = divmod(node, n)
    return lon0 + c * spacing, lat0 + r * spacing


@pytest.fixture
def grid_graph():
    return build_grid_graph()


@pytest.fixture
def city(grid_graph):
    """A CityGraph wrapping a fresh synthetic graph (not yet annotated)."""
    return CityGraph(graph=grid_graph)


@pytest.fixture
def annotated_city(city):
    city.annotate_travel_costs(speed_kmh=18, consumption_wh_per_km=12)
    return city


@pytest.fixture
def model():
    """A small model on a fresh synthetic graph (uniform random demand)."""
    cg = CityGraph(graph=build_grid_graph())
    return GraphBatterySwapModel(
        city_graph=cg, n_riders=3, n_lockers=2, seconds_per_step=10
    )


@pytest.fixture
def tiny_model():
    """A minimal Mesa model exposing only what GraphLocker needs."""
    class TinyModel(Model):
        def __init__(self, seconds_per_step=10):
            super().__init__()
            self.seconds_per_step = seconds_per_step

    return TinyModel()


@pytest.fixture
def locker_csv(tmp_path):
    p = tmp_path / "lockers.csv"
    lon0, lat0 = node_lonlat(0)
    lon8, lat8 = node_lonlat(8)
    p.write_text(
        "locker_id,name,lat,lon,charged_batteries,capacity\n"
        f"0,A,{lat0},{lon0},5,10\n"
        f"1,B,{lat8},{lon8},5,10\n"
    )
    return str(p)


@pytest.fixture
def hotspot_csv(tmp_path):
    p = tmp_path / "hotspots.csv"
    # Centre of the grid, radius large enough to cover all nodes.
    p.write_text(
        "hotspot_id,name,lat,lon,weight,radius_m\n"
        f"0,Center,{LAT0 + SPACING},{LON0 + SPACING},5,500\n"
    )
    return str(p)


@pytest.fixture
def ferry_csv(tmp_path):
    p = tmp_path / "ferries.csv"
    lon0, lat0 = node_lonlat(0)
    lon8, lat8 = node_lonlat(8)
    p.write_text(
        "name,from_lat,from_lon,to_lat,to_lon,crossing_seconds,wait_seconds\n"
        f"F,{lat0},{lon0},{lat8},{lon8},210,180\n"
    )
    return str(p)
