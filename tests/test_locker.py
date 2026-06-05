import pytest

from src.agents.graph_locker import GraphLocker


def make_locker(tiny_model, charged=5, capacity=10, charge_seconds=20):
    return GraphLocker(
        tiny_model, locker_id=0, node_id=1,
        charged_batteries=charged, capacity=capacity,
        charge_seconds=charge_seconds,
    )


def test_initial_state(tiny_model):
    lk = make_locker(tiny_model, charged=5, capacity=10)
    assert lk.charged_batteries == 5
    assert lk.depleted_batteries == 0
    assert lk.total_batteries == 5
    assert lk.capacity == 10


def test_overstock_is_clamped_with_warning(tiny_model):
    with pytest.warns(UserWarning):
        lk = make_locker(tiny_model, charged=15, capacity=10)
    assert lk.charged_batteries == 10


def test_add_depleted_battery_queues_charge(tiny_model):
    lk = make_locker(tiny_model, charged=5, capacity=10)
    lk.add_depleted_battery()
    assert lk.depleted_batteries == 1
    assert lk.charging_queue == [lk.charge_seconds]


def test_add_depleted_respects_capacity(tiny_model):
    lk = make_locker(tiny_model, charged=10, capacity=10)  # full
    lk.add_depleted_battery()
    assert lk.depleted_batteries == 0           # rejected, already full
    assert lk.charging_queue == []


def test_charging_completes_after_enough_time(tiny_model):
    # charge_seconds=20, seconds_per_step=10 -> 2 steps to recharge.
    lk = make_locker(tiny_model, charged=4, capacity=10, charge_seconds=20)
    lk.charged_batteries -= 1          # simulate a swap consuming a charged one
    lk.add_depleted_battery()
    assert lk.charged_batteries == 3 and lk.depleted_batteries == 1

    lk.step()                          # 10s elapsed, not done
    assert lk.depleted_batteries == 1
    lk.step()                          # 20s elapsed, charged
    assert lk.charged_batteries == 4 and lk.depleted_batteries == 0


def test_swap_conserves_total(tiny_model):
    lk = make_locker(tiny_model, charged=5, capacity=10)
    before = lk.total_batteries
    lk.charged_batteries -= 1
    lk.add_depleted_battery()
    assert lk.total_batteries == before
