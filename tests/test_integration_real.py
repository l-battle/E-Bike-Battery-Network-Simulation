"""End-to-end test against the real Amsterdam graph.

Slow and network/cache dependent, so marked `slow` and skipped by default.
Run with: pytest -m slow
"""
import pytest

from src.simulation.graph_model import GraphBatterySwapModel
from src.agents.graph_rider import GraphRider
from src.utils.config import BATTERY_CAPACITY_WH

pytestmark = pytest.mark.slow


@pytest.fixture(scope="module")
def real_model():
    try:
        return GraphBatterySwapModel(
            n_riders=10,
            locker_csv="data/lockers_amsterdam.csv",
            hotspot_csv="data/hotspots_amsterdam.csv",
            ferry_csv="data/ferries_amsterdam.csv",
        )
    except Exception as exc:  # no network / no cache
        pytest.skip(f"Could not load real graph: {exc}")


def test_real_graph_is_strongly_connected(real_model):
    import networkx as nx
    assert nx.is_strongly_connected(real_model.city_graph.graph)


def test_real_model_runs_and_holds_invariants(real_model):
    model = real_model
    for _ in range(200):
        model.step()

    assert len(model.history) >= 200
    for rider in (a for a in model.agents if isinstance(a, GraphRider)):
        assert 0 <= rider.battery_level <= BATTERY_CAPACITY_WH
    for locker in model.graph_lockers:
        assert locker.total_batteries <= locker.capacity


def test_real_ferry_present(real_model):
    ferry_edges = [
        d for _, _, d in real_model.city_graph.graph.edges(data=True)
        if d.get("is_ferry")
    ]
    assert len(ferry_edges) >= 2  # bidirectional
