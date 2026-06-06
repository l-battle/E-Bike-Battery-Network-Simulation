"""Driver: turn sampler draws into dataset rows by running the simulation.

For each draw it places lockers at the sampled layout, computes the layout's
features, runs the sim to steady state, and records the outcome metrics. One
draw -> one row. The collected rows are the surrogate's training table.
"""
from src.environment.city_graph import CityGraph
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


def run_draw(draw, base_graph, settings):
    """Run one sampled experiment and return a flat result row.

    Order matters: the model annotates the graph and builds the demand model in
    its constructor, and features need both -- so features are computed after
    the model is built but before stepping.
    """
    set_seed(draw["seed"])

    # Fresh copy so per-run graph mutations never leak between draws.
    city_graph = CityGraph(graph=base_graph.copy())
    scenario = draw["scenario"]

    model = GraphBatterySwapModel(
        city_graph=city_graph,
        locker_nodes=draw["layout"],
        n_riders=scenario["n_riders"],
        rider_speed_kmh=scenario["rider_speed_kmh"],
        weather=scenario["weather"],
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


def run_dataset(draws, settings=None, base_graph=None, out_stem=None,
                progress=True):
    """Run all draws (reusing one loaded graph) and return result rows.

    If `out_stem` is given, also writes data/experiments/<stem>.csv/.json.
    """
    settings = {**DEFAULT_SETTINGS, **(settings or {})}

    if base_graph is None:
        base_graph = load_base_graph(settings["place_name"])

    rows = []
    for i, draw in enumerate(draws, 1):
        if progress:
            print(f"[{i}/{len(draws)}] combo={draw['combo_id']} seed={draw['seed']}")
        rows.append(run_draw(draw, base_graph, settings))

    if out_stem:
        save_results(rows, out_stem)

    return rows
