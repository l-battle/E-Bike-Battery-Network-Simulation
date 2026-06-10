"""Plots for the AI phase: surrogate accuracy, feature importance, and
placement-optimization results. For the beta report."""
import math

import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import r2_score
from sklearn.inspection import permutation_importance


def plot_parity(y_true, y_pred, targets, ncols=3):
    """Predicted vs actual scatter per target (the 45-degree line = perfect)."""
    nrows = math.ceil(len(targets) / ncols)
    fig, axes = plt.subplots(nrows, ncols, figsize=(4 * ncols, 3.4 * nrows))
    axes = np.array(axes).flatten()

    for ax, t in zip(axes, targets):
        a, p = y_true[t], y_pred[t]
        ax.scatter(a, p, s=12, alpha=0.5)
        lo, hi = min(a.min(), p.min()), max(a.max(), p.max())
        ax.plot([lo, hi], [lo, hi], "k--", lw=1)
        ax.set_title(f"{t}\nR² = {r2_score(a, p):.2f}", fontsize=9)
        ax.set_xlabel("actual")
        ax.set_ylabel("predicted")

    for ax in axes[len(targets):]:
        ax.axis("off")
    fig.suptitle("Surrogate: predicted vs actual (test set)")
    fig.tight_layout()
    return fig


def plot_metric_bars(metrics):
    """Grouped R2 / Spearman bars per target."""
    targets = list(metrics)
    r2 = [metrics[t]["r2"] for t in targets]
    sp = [metrics[t]["spearman"] for t in targets]
    x = np.arange(len(targets))
    w = 0.4

    fig, ax = plt.subplots(figsize=(1.3 * len(targets) + 2, 4))
    ax.bar(x - w / 2, r2, w, label="R²")
    ax.bar(x + w / 2, sp, w, label="Spearman")
    ax.set_xticks(x)
    ax.set_xticklabels(targets, rotation=45, ha="right")
    ax.set_ylim(0, 1)
    ax.set_title("Surrogate accuracy by target")
    ax.legend()
    fig.tight_layout()
    return fig


def plot_feature_importance(surrogate, X_test, y_test, target,
                            n_repeats=10, seed=0):
    """Permutation importance of features for one target."""
    i = surrogate.target_names.index(target)
    estimator = surrogate.model.estimators_[i]
    result = permutation_importance(
        estimator, X_test, y_test[target],
        n_repeats=n_repeats, random_state=seed,
    )
    order = np.argsort(result.importances_mean)
    feats = np.array(X_test.columns)[order]
    imp = result.importances_mean[order]

    fig, ax = plt.subplots(figsize=(6, 0.4 * len(feats) + 1))
    ax.barh(feats, imp, color="tab:green")
    ax.set_xlabel("permutation importance")
    ax.set_title(f"Feature importance: {target}")
    fig.tight_layout()
    return fig


def plot_optimization_curve(history):
    """Objective score vs number of lockers (diminishing returns)."""
    n = [h["n_lockers"] for h in history]
    s = [h["score"] for h in history]
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(n, s, marker="o")
    ax.set_xlabel("number of lockers")
    ax.set_ylabel("objective score")
    ax.set_title("Placement objective vs number of lockers")
    fig.tight_layout()
    return fig


def plot_placement_comparison(labels, values, ylabel="mean stranded riders"):
    """Bar chart comparing optimized vs random placement outcomes."""
    fig, ax = plt.subplots(figsize=(5, 4))
    colors = ["tab:blue"] + ["tab:gray"] * (len(labels) - 1)
    ax.bar(labels, values, color=colors)
    ax.set_ylabel(ylabel)
    ax.set_title("Optimized vs random placement")
    fig.tight_layout()
    return fig
