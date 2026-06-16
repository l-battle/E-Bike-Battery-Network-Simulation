"""Translate simulation outcomes into euros.

Maps per-hour service metrics + a decision's locker count into revenue, costs,
and profit over a horizon. Combined with the risk layer (a distribution of
runs), this yields a financial risk profile for a proposed decision.
All unit prices are placeholder estimates (see config.ECONOMICS).
"""
from src.utils.config import ECONOMICS


def evaluate_economics(metrics, n_lockers, horizon_hours=24, prices=ECONOMICS):
    """Euros over `horizon_hours` for one run's metrics and locker count."""
    revenue = metrics["trips_per_hour"] * horizon_hours * prices["revenue_per_delivery"]

    locker_cost = n_lockers * prices["cost_per_locker_per_day"] * (horizon_hours / 24)
    stranding_cost = (
        metrics["stranded_per_hour"] * horizon_hours * prices["cost_per_stranded"]
    )
    swap_cost = metrics["swaps_per_hour"] * horizon_hours * prices["cost_per_swap"]
    total_cost = locker_cost + stranding_cost + swap_cost

    return {
        "revenue": revenue,
        "locker_cost": locker_cost,
        "stranding_cost": stranding_cost,
        "swap_cost": swap_cost,
        "total_cost": total_cost,
        "profit": revenue - total_cost,
    }


def add_economics(df, horizon_hours=24, prices=ECONOMICS, n_lockers_col="n_lockers_actual"):
    """Add revenue/cost/profit columns to a DataFrame of run metrics
    (e.g. the output of evaluate_decision)."""
    econ = df.apply(
        lambda row: evaluate_economics(row, row[n_lockers_col], horizon_hours, prices),
        axis=1, result_type="expand",
    )
    return df.join(econ)
