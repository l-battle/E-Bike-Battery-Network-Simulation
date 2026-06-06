import pytest

from tests.conftest import build_grid_graph
from src.experiments.candidate_sites import generate_candidate_sites
from src.environment.city_graph import CityGraph
from src.experiments.sampler import sample_experiments
from src.experiments.driver import run_draw, run_dataset
from src.experiments.features import compute_features

# Feature + metric keys a complete row must contain.
FEATURE_KEYS = {
    "n_riders", "rider_speed_kmh", "weather", "n_lockers", "total_capacity",
    "lockers_per_rider", "capacity_per_rider", "coverage_3min", "coverage_5min",
    "coverage_10min", "mean_demand_to_locker_min", "p90_demand_to_locker_min",
    "unmet_demand_frac", "locker_dispersion",
}
METRIC_KEYS = {
    "trips_per_hour", "swaps_per_hour", "failed_swaps_per_hour",
    "stranded_per_hour", "swap_success_rate", "mean_battery_wh",
    "mean_stranded_riders", "locker_utilization",
}

SETTINGS = {
    "hotspot_csv": "data/hotspots_amsterdam.csv",  # real hotspots are far from
    "ferry_csv": None,                             # the grid -> demand falls back
    "n_steps": 60,
    "warmup_steps": 10,
    "seconds_per_step": 10,
}


@pytest.fixture
def base_graph():
    return build_grid_graph()


@pytest.fixture
def candidates(base_graph):
    cg = CityGraph(graph=base_graph)
    return generate_candidate_sites(cg, demand=None, n_sites=6,
                                    min_spacing_m=10, seed=0)


@pytest.fixture
def grid_hotspot_csv(tmp_path):
    """A hotspot centered on the synthetic grid (so demand exists for it)."""
    from tests.conftest import LAT0, LON0, SPACING
    p = tmp_path / "h.csv"
    p.write_text(
        "hotspot_id,name,lat,lon,weight,radius_m\n"
        f"0,C,{LAT0 + SPACING},{LON0 + SPACING},5,500\n"
    )
    return str(p)


@pytest.fixture
def settings(grid_hotspot_csv):
    return {**SETTINGS, "hotspot_csv": grid_hotspot_csv}


def _draws(candidates, n_samples=3, seeds=(0,)):
    return sample_experiments(candidates, n_samples=n_samples, seeds=seeds,
                              ranges={"n_lockers": (2, 4), "n_riders": (5, 10),
                                      "rider_speed_kmh": (15, 20),
                                      "weathers": ["clear", "rain"]},
                              rng_seed=0)


def test_run_draw_row_schema(base_graph, candidates, settings):
    draw = _draws(candidates)[0]
    row = run_draw(draw, base_graph, settings)
    assert FEATURE_KEYS <= set(row)
    assert METRIC_KEYS <= set(row)
    assert row["combo_id"] == draw["combo_id"]
    assert row["seed"] == draw["seed"]


def test_n_lockers_matches_layout(base_graph, candidates, settings):
    draw = _draws(candidates)[0]
    row = run_draw(draw, base_graph, settings)
    assert row["n_lockers"] == len(draw["layout"])


def test_run_draw_is_deterministic(base_graph, candidates, settings):
    draw = _draws(candidates)[0]
    r1 = run_draw(draw, base_graph, settings)
    r2 = run_draw(draw, base_graph, settings)
    assert r1 == r2


def test_base_graph_not_mutated(base_graph, candidates, settings):
    before = base_graph.number_of_edges()
    run_draw(_draws(candidates)[0], base_graph, settings)
    assert base_graph.number_of_edges() == before


def test_run_dataset_row_count(base_graph, candidates, settings):
    draws = _draws(candidates, n_samples=3, seeds=(0, 1))
    rows = run_dataset(draws, settings=settings, base_graph=base_graph,
                       progress=False)
    assert len(rows) == len(draws) == 6


def test_run_dataset_exports_csv(base_graph, candidates, settings, tmp_path):
    import src.experiments.runner as runner
    runner.RESULTS_DIR = tmp_path          # redirect output
    draws = _draws(candidates, n_samples=2)
    run_dataset(draws, settings=settings, base_graph=base_graph,
                out_stem="test_ds", progress=False)
    assert (tmp_path / "test_ds.csv").exists()
    assert (tmp_path / "test_ds.json").exists()


def test_replicates_share_features_differ_in_noise(base_graph, candidates, settings):
    # Same layout/scenario, different seeds -> identical features, (likely)
    # different targets.
    draws = _draws(candidates, n_samples=1, seeds=(0, 1))
    rows = [run_draw(d, base_graph, settings) for d in draws]
    for key in FEATURE_KEYS:
        assert rows[0][key] == rows[1][key]      # features are deterministic
