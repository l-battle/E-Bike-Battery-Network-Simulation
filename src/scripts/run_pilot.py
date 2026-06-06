"""Generate a pilot training dataset for the surrogate.

Loads the real graph once, builds candidate sites, samples experiments, runs
them through the driver, and writes data/experiments/pilot.csv.

Run with:  python -m src.scripts.run_pilot

Start small to validate, then scale up N_SAMPLES / SEEDS for the full dataset.
"""
from src.environment.city_graph import CityGraph
from src.environment.demand import DemandModel
from src.experiments.candidate_sites import generate_candidate_sites
from src.experiments.sampler import sample_experiments
from src.experiments.driver import run_dataset
from src.experiments.runner import load_base_graph

N_CANDIDATES = 40
N_SAMPLES = 120          # unique (layout, scenario) combos
SEEDS = (0,)             # add seeds (e.g. (0, 1, 2)) for replicates later
HOTSPOT_CSV = "data/hotspots_amsterdam.csv"

# 1. Load the real Amsterdam graph ONCE (reused for every run).
base_graph = load_base_graph("Amsterdam, Netherlands")

# 2. Build candidate sites (needs the demand model to seed from).
cg = CityGraph(graph=base_graph)
demand = DemandModel(cg, HOTSPOT_CSV)
candidates = generate_candidate_sites(cg, demand=demand,
                                      n_sites=N_CANDIDATES, seed=0)
print(f"Generated {len(candidates)} candidate sites.")

# 3. Sample experiments.
draws = sample_experiments(candidates, n_samples=N_SAMPLES, seeds=SEEDS)
print(f"Sampled {len(draws)} experiments. Running...")

# 4. Run them and export the dataset.
rows = run_dataset(
    draws,
    settings={"hotspot_csv": HOTSPOT_CSV},
    base_graph=base_graph,
    out_stem="pilot",
)
print(f"\nDone. {len(rows)} rows -> data/experiments/pilot.csv")
