"""Generate a training dataset for the surrogate.

Loads the real graph once per worker, builds candidate sites, samples
experiments, runs them through the driver (in parallel), and writes
data/experiments/<OUT_STEM>.csv.

Run with:  python -m src.scripts.run_pilot

The __main__ guard is required: with parallel workers (spawn), the module is
re-imported in each worker, so top-level work must not run there.
"""
import os

from src.environment.city_graph import CityGraph
from src.environment.demand import DemandModel
from src.experiments.candidate_sites import generate_candidate_sites
from src.experiments.sampler import sample_experiments
from src.experiments.driver import run_dataset
from src.experiments.runner import load_base_graph

N_CANDIDATES = 40
N_SAMPLES = 120          # unique (layout, scenario) combos
SEEDS = (0,)             # add seeds for replicates
HOTSPOT_CSV = "data/hotspots_amsterdam.csv"
OUT_STEM = "pilot"
N_WORKERS = max(1, (os.cpu_count() or 2) - 1)


def main():
    # Candidate sites need the graph + demand to seed from (built once here).
    base_graph = load_base_graph("Amsterdam, Netherlands")
    cg = CityGraph(graph=base_graph)
    demand = DemandModel(cg, HOTSPOT_CSV)
    candidates = generate_candidate_sites(cg, demand=demand,
                                          n_sites=N_CANDIDATES, seed=0)
    print(f"{len(candidates)} candidate sites.")

    draws = sample_experiments(candidates, n_samples=N_SAMPLES, seeds=SEEDS)
    print(f"Running {len(draws)} experiments on {N_WORKERS} workers...")

    rows = run_dataset(draws, out_stem=OUT_STEM, n_workers=N_WORKERS)
    print(f"\nDone. {len(rows)} rows -> data/experiments/{OUT_STEM}.csv")


if __name__ == "__main__":
    main()
