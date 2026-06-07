import pandas as pd
import pytest

from src.ai.objective import Objective

# Reference data the objective fits its normalisation ranges on.
FIT_Y = pd.DataFrame({
    "stranded_per_hour":  [0, 5, 10],
    "swap_success_rate":  [0.5, 0.75, 1.0],
    "locker_utilization": [0.0, 0.4, 0.8],
})

GOOD = {"stranded_per_hour": 0, "swap_success_rate": 1.0, "locker_utilization": 0.8}
BAD = {"stranded_per_hour": 10, "swap_success_rate": 0.5, "locker_utilization": 0.0}


def fitted(weights=None):
    return Objective(weights=weights).fit(FIT_Y)


def test_score_before_fit_raises():
    with pytest.raises(ValueError):
        Objective().score(GOOD)


def test_good_beats_bad():
    obj = fitted()
    assert obj.score(GOOD) > obj.score(BAD)


def test_scores_within_bounds():
    obj = fitted()
    for pred in (GOOD, BAD, {"stranded_per_hour": 3,
                             "swap_success_rate": 0.7,
                             "locker_utilization": 0.3}):
        assert 0.0 <= obj.score(pred) <= 1.0


def test_best_and_worst_extremes():
    obj = fitted()
    assert obj.score(GOOD) == pytest.approx(1.0)
    assert obj.score(BAD) == pytest.approx(0.0)


def test_predictions_outside_range_are_clipped():
    obj = fitted()
    # better than any training row -> clipped, still <= 1
    extreme = {"stranded_per_hour": -5, "swap_success_rate": 2.0,
               "locker_utilization": 5.0}
    assert obj.score(extreme) == pytest.approx(1.0)


def test_weights_isolate_a_target():
    # Only strandings matter -> two preds with same stranded but different
    # success/util should score equal.
    obj = fitted(weights={"stranded_per_hour": 1.0,
                          "swap_success_rate": 0.0,
                          "locker_utilization": 0.0})
    a = {"stranded_per_hour": 5, "swap_success_rate": 1.0, "locker_utilization": 0.8}
    b = {"stranded_per_hour": 5, "swap_success_rate": 0.5, "locker_utilization": 0.0}
    assert obj.score(a) == pytest.approx(obj.score(b))


def test_constant_target_does_not_crash():
    y = FIT_Y.copy()
    y["locker_utilization"] = 0.5            # constant column
    obj = Objective().fit(y)
    score = obj.score({"stranded_per_hour": 0, "swap_success_rate": 1.0,
                       "locker_utilization": 0.5})
    assert 0.0 <= score <= 1.0


def test_extra_prediction_keys_are_ignored():
    obj = fitted()
    pred = dict(GOOD, trips_per_hour=999, mean_battery_wh=123)  # extra columns
    assert obj.score(pred) == pytest.approx(1.0)
