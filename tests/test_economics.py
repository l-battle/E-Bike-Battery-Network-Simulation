import pandas as pd

from src.experiments.economics import evaluate_economics, add_economics

PRICES = {
    "revenue_per_delivery": 2.0,
    "cost_per_locker_per_day": 10.0,
    "cost_per_stranded": 5.0,
    "cost_per_swap": 0.5,
}


def metrics(trips=10.0, stranded=1.0, swaps=4.0):
    return {"trips_per_hour": trips, "stranded_per_hour": stranded,
            "swaps_per_hour": swaps}


def test_economics_arithmetic():
    e = evaluate_economics(metrics(), n_lockers=3, horizon_hours=24, prices=PRICES)
    assert e["revenue"] == 10.0 * 24 * 2.0              # 480
    assert e["locker_cost"] == 3 * 10.0                 # 30 (one day)
    assert e["stranding_cost"] == 1.0 * 24 * 5.0        # 120
    assert e["swap_cost"] == 4.0 * 24 * 0.5             # 48
    assert e["profit"] == 480 - (30 + 120 + 48)


def test_more_strandings_reduce_profit():
    good = evaluate_economics(metrics(stranded=0.0), 3, prices=PRICES)
    bad = evaluate_economics(metrics(stranded=5.0), 3, prices=PRICES)
    assert bad["profit"] < good["profit"]


def test_more_lockers_add_cost():
    few = evaluate_economics(metrics(), n_lockers=2, prices=PRICES)
    many = evaluate_economics(metrics(), n_lockers=20, prices=PRICES)
    assert many["locker_cost"] > few["locker_cost"]
    assert many["profit"] < few["profit"]


def test_add_economics_columns():
    df = pd.DataFrame([
        {"trips_per_hour": 10, "stranded_per_hour": 1, "swaps_per_hour": 4,
         "n_lockers_actual": 3},
        {"trips_per_hour": 20, "stranded_per_hour": 0, "swaps_per_hour": 8,
         "n_lockers_actual": 5},
    ])
    out = add_economics(df, prices=PRICES)
    assert {"revenue", "total_cost", "profit"} <= set(out.columns)
    assert len(out) == 2
    # second row has more trips and no strandings -> higher profit
    assert out.iloc[1]["profit"] > out.iloc[0]["profit"]
