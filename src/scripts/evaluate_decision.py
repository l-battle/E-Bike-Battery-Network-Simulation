"""Evaluate a proposed decision: expected outcome + financial risk profile.

Runs the decision across seeds and weather conditions, attaches economics, and
reports the distribution of profit and service outcomes -- the leading,
risk-aware measure that complements a P&L. Saves a profit-distribution plot.

Run with:  python -m src.scripts.evaluate_decision
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")

from src.experiments.config import ExperimentConfig
from src.experiments.risk import (
    evaluate_decision, risk_profile, probability_below, value_at_risk,
)
from src.experiments.economics import add_economics
from src.visualization.ai_plots import plot_risk_distribution

OUT = Path("data/exports/report")

# The decision under evaluation (locker network + operating scenario).
DECISION = ExperimentConfig(
    name="decision",
    n_riders=30,
    locker_csv="data/lockers_amsterdam.csv",
    hotspot_csv="data/hotspots_amsterdam.csv",
    ferry_csv="data/ferries_amsterdam.csv",
    n_steps=2000,
    warmup_steps=1200,
)
SEEDS = range(5)
WEATHERS = ["clear", "rain", "snow"]
HORIZON_HOURS = 24


def main():
    print(f"Evaluating decision across {len(list(SEEDS))} seeds x "
          f"{len(WEATHERS)} weathers...")
    df = evaluate_decision(DECISION, seeds=SEEDS, weathers=WEATHERS, progress=True)
    df = add_economics(df, horizon_hours=HORIZON_HOURS)

    print("\n--- Service & financial risk profile ---")
    for metric in ["delivery_success_rate", "stranded_per_hour", "profit"]:
        p = risk_profile(df, metric)
        print(f"{metric:22s} mean={p['mean']:.2f}  p10={p['p10']:.2f}  "
              f"p90={p['p90']:.2f}")

    print(f"\nProbability of a loss (profit < 0): "
          f"{probability_below(df, 'profit', 0):.0%}")
    print(f"Worst-case (90th-pct) stranded/hr: "
          f"{value_at_risk(df, 'stranded_per_hour', 0.9):.2f}")

    OUT.mkdir(parents=True, exist_ok=True)
    plot_risk_distribution(df["profit"], "daily profit (EUR)", threshold=0).savefig(
        OUT / "decision_profit_risk.png", dpi=90)
    print(f"\nSaved profit-risk plot to {OUT}/decision_profit_risk.png")


if __name__ == "__main__":
    main()
