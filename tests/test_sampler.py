import random

from src.experiments.sampler import (
    DEFAULT_RANGES, sample_layout, sample_scenario, sample_experiments,
)

CANDIDATES = [{"node_id": i} for i in range(10)]


# ---- sample_layout ----

def test_sample_layout_size_and_uniqueness():
    rng = random.Random(0)
    ids = [c["node_id"] for c in CANDIDATES]
    for _ in range(20):
        layout = sample_layout(ids, rng, k_min=2, k_max=5)
        assert 2 <= len(layout) <= 5
        assert len(set(layout)) == len(layout)        # no duplicate sites
        assert all(n in ids for n in layout)


def test_sample_layout_clamps_to_candidate_count():
    rng = random.Random(0)
    ids = [1, 2, 3]
    layout = sample_layout(ids, rng, k_min=3, k_max=99)
    assert len(layout) == 3


# ---- sample_scenario ----

def test_sample_scenario_in_range():
    rng = random.Random(0)
    for _ in range(20):
        s = sample_scenario(rng, DEFAULT_RANGES)
        lo, hi = DEFAULT_RANGES["n_riders"]
        assert lo <= s["n_riders"] <= hi
        lo, hi = DEFAULT_RANGES["rider_speed_kmh"]
        assert lo <= s["rider_speed_kmh"] <= hi
        assert s["weather"] in DEFAULT_RANGES["weathers"]


# ---- sample_experiments ----

def test_count_is_samples_times_seeds():
    draws = sample_experiments(CANDIDATES, n_samples=5, seeds=(0, 1, 2))
    assert len(draws) == 5 * 3


def test_is_deterministic():
    a = sample_experiments(CANDIDATES, n_samples=5, seeds=(0, 1), rng_seed=7)
    b = sample_experiments(CANDIDATES, n_samples=5, seeds=(0, 1), rng_seed=7)
    assert a == b


def test_different_rng_seed_differs():
    a = sample_experiments(CANDIDATES, n_samples=5, seeds=(0,), rng_seed=1)
    b = sample_experiments(CANDIDATES, n_samples=5, seeds=(0,), rng_seed=2)
    assert a != b


def test_replicates_share_layout_and_scenario():
    draws = sample_experiments(CANDIDATES, n_samples=4, seeds=(0, 1, 2))
    by_combo = {}
    for d in draws:
        by_combo.setdefault(d["combo_id"], []).append(d)

    for combo_draws in by_combo.values():
        layouts = [tuple(d["layout"]) for d in combo_draws]
        scenarios = [tuple(sorted(d["scenario"].items())) for d in combo_draws]
        assert len(set(layouts)) == 1        # identical layout across seeds
        assert len(set(scenarios)) == 1      # identical scenario across seeds
        assert {d["seed"] for d in combo_draws} == {0, 1, 2}  # but different seeds


def test_draw_structure():
    draws = sample_experiments(CANDIDATES, n_samples=2, seeds=(0,))
    d = draws[0]
    assert set(d) == {"combo_id", "seed", "layout", "scenario"}
    assert isinstance(d["layout"], list)
    assert isinstance(d["scenario"], dict)
