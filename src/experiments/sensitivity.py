"""One-at-a-time (OAT) sensitivity analysis.

Vary each parameter across a range while holding the others at a baseline,
replicated over seeds. Used to validate that the simulator responds to changes
in the right direction and magnitude, and to rank which parameters matter most.
"""
import pandas as pd

from src.experiments.runner import run_experiment, load_base_graph


def run_sensitivity(base_config, sweeps, seeds, base_graph=None,
                    place_name="Amsterdam, Netherlands", progress=True):
    """Run an OAT sweep.

    `sweeps` maps a config field to either a list of values, or a dict
    {"values": [...], "overrides": {...}} where overrides are extra config
    changes needed for that sweep (e.g. locker_csv=None to vary n_lockers).

    Returns result rows, each tagged with `swept_param` and `swept_value`.
    """
    if base_graph is None:
        base_graph = load_base_graph(place_name)

    rows = []
    for param, spec in sweeps.items():
        if isinstance(spec, dict):
            values = spec["values"]
            overrides = spec.get("overrides", {})
        else:
            values, overrides = spec, {}

        for value in values:
            for seed in seeds:
                cfg = base_config.with_overrides(
                    seed=seed, name=f"sa_{param}={value}",
                    **overrides, **{param: value},
                )
                row = run_experiment(cfg, base_graph=base_graph)
                row["swept_param"] = param
                row["swept_value"] = value
                rows.append(row)
                if progress:
                    print(f"  {param}={value} seed={seed} done")

    return rows


def sensitivity_table(rows, metrics):
    """Mean/std of each metric per (swept_param, swept_value)."""
    df = pd.DataFrame(rows)
    return (
        df.groupby(["swept_param", "swept_value"])[metrics]
        .agg(["mean", "std"])
        .reset_index()
    )


def impact_ranking(rows, metric):
    """Rank parameters by how much they move `metric` across their range.

    Returns a list of (param, spread) sorted high to low, where spread is
    max(mean) - min(mean) of the metric over the parameter's swept values.
    """
    df = pd.DataFrame(rows)
    spreads = {}
    for param, group in df.groupby("swept_param"):
        means = group.groupby("swept_value")[metric].mean()
        spreads[param] = float(means.max() - means.min())
    return sorted(spreads.items(), key=lambda kv: kv[1], reverse=True)
