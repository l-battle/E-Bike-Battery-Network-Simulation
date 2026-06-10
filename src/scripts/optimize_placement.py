"""Recommend a locker placement using the trained surrogate + greedy optimizer,
then close the loop by verifying it in the real simulation.

Run with:  python -m src.scripts.optimize_placement
"""
import random
import statistics
from pathlib import Path

import matplotlib
matplotlib.use("Agg")

from src.environment.city_graph import CityGraph
from src.environment.demand import DemandModel
from src.experiments.candidate_sites import generate_candidate_sites
from src.experiments.runner import load_base_graph
from src.experiments.driver import run_draw
from src.ai.dataset import make_dataset
from src.ai.surrogate import Surrogate
from src.ai.objective import Objective
from src.ai.optimizer import greedy_optimize
from src.visualization.ai_plots import (
    plot_optimization_curve, plot_placement_comparison,
)

DATASET = "data/experiments/dataset_v1.csv"
SURROGATE = "data/experiments/surrogate_pilot.joblib"
HOTSPOT_CSV = "data/hotspots_amsterdam.csv"

# Optimise placement for this scenario.
SCENARIO = {"n_riders": 30, "rider_speed_kmh": 18, "weather": "clear"}
BUDGET = 25
COMPARE_K = 6                 # budget at which to test placement vs random
SEEDS = [0, 1, 2]            # seed-averaged comparison (single runs are noisy)
OUT = Path("data/exports/report")

# Optimise the well-predicted, meaningful, non-degenerate service signal
# (mean stranded riders, Spearman ~0.98). swap_success_rate is excluded: it is
# degenerate (=1.0 when no swap attempts), which rewards under-provisioned
# layouts. locker_utilization is excluded for now (weaker signal).
DIRECTIONS = {
    "mean_stranded_riders": "min",
}


def main():
    base_graph = load_base_graph("Amsterdam, Netherlands")
    cg = CityGraph(graph=base_graph)
    cg.annotate_travel_costs(SCENARIO["rider_speed_kmh"], 12)
    demand = DemandModel(cg, HOTSPOT_CSV)
    candidates = generate_candidate_sites(cg, demand=demand, n_sites=40, seed=0)

    # feature_names must match how the surrogate was trained.
    ds = make_dataset(DATASET, test_size=0.25, seed=0)
    surrogate = Surrogate.load(SURROGATE)
    objective = Objective(directions=DIRECTIONS).fit(ds.y_train)

    print(f"Optimising placement for {SCENARIO} (budget {BUDGET})...\n")
    chosen, history = greedy_optimize(
        candidate_sites=candidates, scenario=SCENARIO, surrogate=surrogate,
        objective=objective, feature_names=ds.feature_names,
        city_graph=cg, demand=demand, budget=BUDGET,
    )

    print(f"Recommended {len(chosen)} lockers (in priority order):")
    coords = {c["node_id"]: (c["lat"], c["lon"]) for c in candidates}
    for rank, node in enumerate(chosen, 1):
        lat, lon = coords[node]
        print(f"  {rank:2d}. node {node}  ({lat:.4f}, {lon:.4f})")

    OUT.mkdir(parents=True, exist_ok=True)
    plot_optimization_curve(history).savefig(OUT / "optimization_curve.png", dpi=90)

    # --- close the loop: optimized vs random placement at a constrained budget,
    #     averaged over seeds (single runs are too noisy to compare) ---
    settings = {"hotspot_csv": HOTSPOT_CSV, "ferry_csv": "data/ferries_amsterdam.csv",
                "n_steps": 2000, "warmup_steps": 1200, "seconds_per_step": 10}
    metric = "mean_stranded_riders"

    optimized_k = history[COMPARE_K]["layout"]      # top-K greedy picks
    all_nodes = [c["node_id"] for c in candidates]
    rng = random.Random(1)

    def avg_metric(layout):
        vals = [
            run_draw({"combo_id": 0, "seed": s, "layout": layout,
                      "scenario": SCENARIO}, base_graph, settings, demand=demand)[metric]
            for s in SEEDS
        ]
        return statistics.mean(vals)

    print(f"\nPlacement value at {COMPARE_K} lockers ({len(SEEDS)} seeds, "
          f"{metric}):")
    opt_val = avg_metric(optimized_k)
    rand_vals = [avg_metric(rng.sample(all_nodes, COMPARE_K)) for _ in range(3)]
    rand_mean = statistics.mean(rand_vals)
    print(f"  optimised: {opt_val:.2f}")
    print(f"  random:    {rand_mean:.2f}  ({['%.2f' % r for r in rand_vals]})")
    print(f"  improvement: {100 * (rand_mean - opt_val) / rand_mean:.0f}%")

    plot_placement_comparison(
        ["optimised", "random #1", "random #2", "random #3"],
        [opt_val, *rand_vals],
    ).savefig(OUT / "placement_comparison.png", dpi=90)
    print(f"\nSaved plots to {OUT}/")


if __name__ == "__main__":
    main()
