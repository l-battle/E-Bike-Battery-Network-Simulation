"""Decision evaluation under uncertainty.

A decision (an ExperimentConfig) is run across many seeds and optionally a set
of weather conditions, producing a distribution of outcomes rather than a point
estimate -- the basis for a leading, risk-aware decision-support measure.
"""
import pandas as pd

from src.experiments.runner import run_experiment, load_base_graph


def evaluate_decision(config, seeds=(0, 1, 2, 3, 4), weathers=None,
                      base_graph=None, progress=False):
    """Run `config` across seeds (x weathers) and return one row per run."""
    if base_graph is None:
        base_graph = load_base_graph(config.place_name)

    conditions = [(s, w) for s in seeds for w in (weathers or [config.weather])]
    rows = []
    for i, (seed, weather) in enumerate(conditions, 1):
        if progress:
            print(f"[{i}/{len(conditions)}] seed={seed} weather={weather}")
        run_config = config.with_overrides(seed=seed, weather=weather)
        rows.append(run_experiment(run_config, base_graph=base_graph))
    return pd.DataFrame(rows)


def risk_profile(df, metric):
    """Distribution summary of `metric` across the runs."""
    s = df[metric]
    return {
        "mean": float(s.mean()),
        "std": float(s.std()),
        "min": float(s.min()),
        "p10": float(s.quantile(0.10)),
        "p50": float(s.median()),
        "p90": float(s.quantile(0.90)),
        "max": float(s.max()),
    }


def probability_exceeds(df, metric, threshold):
    """Risk metric: probability that `metric` exceeds `threshold`
    (e.g. probability stranded_per_hour is worse than an acceptable level)."""
    return float((df[metric] > threshold).mean())


def value_at_risk(df, metric, quantile=0.90):
    """The metric value at a tail quantile -- a worst-case service level."""
    return float(df[metric].quantile(quantile))
