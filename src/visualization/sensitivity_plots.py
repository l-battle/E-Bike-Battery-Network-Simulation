"""Plots for one-at-a-time sensitivity analysis."""
import matplotlib.pyplot as plt
import pandas as pd

from src.experiments.sensitivity import impact_ranking


def _is_numeric(values):
    return all(isinstance(v, (int, float)) for v in values)


def plot_parameter_response(rows, param, metrics):
    """Response of each metric to one parameter (mean +/- std over seeds)."""
    df = pd.DataFrame([r for r in rows if r["swept_param"] == param])
    agg = df.groupby("swept_value")[metrics].agg(["mean", "std"])
    x = list(agg.index)

    fig, axes = plt.subplots(1, len(metrics), figsize=(4 * len(metrics), 3.5))
    if len(metrics) == 1:
        axes = [axes]

    for ax, metric in zip(axes, metrics):
        means = agg[(metric, "mean")].values
        stds = agg[(metric, "std")].fillna(0).values
        if _is_numeric(x):
            ax.errorbar(x, means, yerr=stds, marker="o", capsize=3)
        else:
            ax.bar([str(v) for v in x], means, yerr=stds, capsize=3)
        ax.set_xlabel(param)
        ax.set_title(metric.replace("_", " "))

    fig.suptitle(f"Sensitivity to {param}")
    fig.tight_layout()
    return fig


def plot_tornado(rows, metric):
    """Horizontal bar chart ranking parameters by their impact on `metric`."""
    ranking = impact_ranking(rows, metric)
    params = [p for p, _ in ranking][::-1]
    spreads = [s for _, s in ranking][::-1]

    fig, ax = plt.subplots(figsize=(6, 0.6 * len(params) + 1))
    ax.barh(params, spreads, color="tab:purple")
    ax.set_xlabel(f"Range of {metric.replace('_', ' ')} (max - min)")
    ax.set_title(f"Parameter impact on {metric.replace('_', ' ')}")
    fig.tight_layout()
    return fig


def show_sensitivity(rows, metrics, tornado_metric):
    for param in dict.fromkeys(r["swept_param"] for r in rows):
        plot_parameter_response(rows, param, metrics)
    plot_tornado(rows, tornado_metric)
    plt.show()
