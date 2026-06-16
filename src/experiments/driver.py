"""Driver: turn sampler draws into dataset rows by running the simulation.

For each draw it places lockers at the sampled layout, computes the layout's
features, runs the sim to steady state, and records the outcome metrics. One
draw -> one row. The collected rows are the surrogate's training table.

Optimisations for large sweeps:
  - the demand model is built once and reused across runs (not rebuilt each run)
  - runs can be executed in parallel across CPU cores (n_workers)
"""
import multiprocessing as mp

from src.environment.city_graph import CityGraph
from src.environment.demand import DemandModel
from src.simulation.graph_model import GraphBatterySwapModel
from src.experiments.features import compute_features
from src.experiments.runner import (
    set_seed, load_base_graph, summarize, save_results,
)

DEFAULT_SETTINGS = {
    "place_name": "Amsterdam, Netherlands",
    "hotspot_csv": "data/hotspots_amsterdam.csv",
    "ferry_csv": "data/ferries_amsterdam.csv",
    "n_steps": 2000,
    "warmup_steps": 1200,        # > recharge cycle (~1080 steps) for steady state
    "seconds_per_step": 10,
}


def run_draw(draw, base_graph, settings, demand=None, copy_graph=True):
    """Run one sampled experiment and return a flat result row.

    A prebuilt `demand` is reused if given (avoids rebuilding it every run).
    Features are computed after the model is built (it annotates the graph)
    but before stepping.

    `copy_graph=True` (default) isolates each run with a fresh graph copy.
    Set `copy_graph=False` to reuse `base_graph` in place -- safe when the
    caller owns a private graph (e.g. a parallel worker) and runs sequentially,
    since cost annotation is deterministic and ferry insertion is idempotent.
    Avoiding the copy removes the dominant memory/time cost in large sweeps.
    """
    set_seed(draw["seed"])

    graph = base_graph.copy() if copy_graph else base_graph
    city_graph = CityGraph(graph=graph)
    scenario = draw["scenario"]

    model = GraphBatterySwapModel(
        city_graph=city_graph,
        locker_nodes=draw["layout"],
        n_riders=scenario["n_riders"],
        rider_speed_kmh=scenario["rider_speed_kmh"],
        weather=scenario["weather"],
        demand=demand,
        hotspot_csv=settings["hotspot_csv"],
        ferry_csv=settings["ferry_csv"],
        seconds_per_step=settings["seconds_per_step"],
    )

    features = compute_features(
        model.city_graph, model.demand, draw["layout"], scenario
    )

    for _ in range(settings["n_steps"]):
        model.step()

    metrics = summarize(
        model, settings["warmup_steps"], settings["seconds_per_step"]
    )

    return {
        "combo_id": draw["combo_id"],
        "seed": draw["seed"],
        **features,
        **metrics,
    }


# --- parallel execution: per-worker graph + demand live in module globals ---
_WORKER = {}


def _init_worker(place_name, hotspot_csv):
    """Each worker loads the graph and builds demand once, then reuses them."""
    graph = load_base_graph(place_name)
    cg = CityGraph(graph=graph)
    _WORKER["graph"] = graph
    _WORKER["demand"] = DemandModel(cg, hotspot_csv) if hotspot_csv else None


def _worker_run(args):
    draw, settings = args
    # The worker owns its graph and runs draws sequentially, so reuse it in
    # place (no per-run copy) -- the big speed/memory win for large sweeps.
    return run_draw(draw, _WORKER["graph"], settings,
                    demand=_WORKER["demand"], copy_graph=False)


def run_dataset(draws, settings=None, base_graph=None, out_stem=None,
                n_workers=1, progress=True):
    """Run all draws and return result rows.

    n_workers > 1 runs draws in parallel (each worker loads the graph + demand
    once). If out_stem is given, also writes data/experiments/<stem>.csv/.json.
    """
    settings = {**DEFAULT_SETTINGS, **(settings or {})}

    if n_workers > 1:
        with mp.Pool(
            n_workers,
            initializer=_init_worker,
            initargs=(settings["place_name"], settings["hotspot_csv"]),
        ) as pool:
            rows = pool.map(_worker_run, [(d, settings) for d in draws])
    else:
        if base_graph is None:
            base_graph = load_base_graph(settings["place_name"])
        # Build demand once and reuse across all runs.
        demand = None
        if settings["hotspot_csv"]:
            demand = DemandModel(CityGraph(graph=base_graph), settings["hotspot_csv"])

        rows = []
        for i, draw in enumerate(draws, 1):
            if progress:
                print(f"[{i}/{len(draws)}] combo={draw['combo_id']} seed={draw['seed']}")
            rows.append(run_draw(draw, base_graph, settings, demand=demand))

    if out_stem:
        save_results(rows, out_stem)

    return rows
