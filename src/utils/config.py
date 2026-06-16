# Battery model in physical units (watt-hours), so values are checkable
# against real specs. See docs/calibration.md. Best estimates pending real
# data: 500 Wh capacity at 12 Wh/km -> ~42 km full range, ~33 km to threshold.
BATTERY_CAPACITY_WH = 500.0
CONSUMPTION_WH_PER_KM = 12.0
BATTERY_THRESHOLD_FRACTION = 0.20
BATTERY_THRESHOLD_WH = BATTERY_CAPACITY_WH * BATTERY_THRESHOLD_FRACTION

# Time / speed model
TIME_STEP_SECONDS = 10      # simulated seconds elapsed per model step
DEFAULT_SPEED_KMH = 18      # rider cruising speed (e-bike)

# Weather presets. Each scales edge travel_time (slower riding) and
# battery_cost (more drain) by a global factor. 1.0 = no effect. Because the
# factors are global they do not change which route is fastest, so routing is
# unaffected and no re-annotation is needed.
DEFAULT_WEATHER = "clear"
WEATHER_PRESETS = {
    "clear": {"travel_time_factor": 1.00, "battery_factor": 1.00},
    "rain":  {"travel_time_factor": 1.12, "battery_factor": 1.08},
    "wind":  {"travel_time_factor": 1.05, "battery_factor": 1.20},
    "snow":  {"travel_time_factor": 1.45, "battery_factor": 1.30},
    "heat":  {"travel_time_factor": 1.03, "battery_factor": 1.05},
}

# Locker battery economy
DEFAULT_CHARGE_SECONDS = int(3.5 * 3600)   # time to recharge one depleted battery
DEFAULT_CHARGED_BATTERIES = 5         # charged batteries a locker starts with
DEFAULT_LOCKER_CAPACITY = 10          # max total batteries (charged + depleted)

# Real locker hardware comes in these slot capacities.
LOCKER_CAPACITY_TYPES = (7, 8, 10)

# Unit economics (EUR) for translating service outcomes into profit. These are
# placeholder estimates pending real operator figures; isolated here so they can
# be replaced without touching the model.
ECONOMICS = {
    "revenue_per_delivery": 1.50,     # net margin per completed delivery
    "cost_per_locker_per_day": 20.0,  # amortised capex + opex per locker
    "cost_per_stranded": 8.0,         # lost order + recovery per stranding
    "cost_per_swap": 0.30,            # charging energy + battery wear per swap
}

# Warn if a CSV locker snaps further than this (metres) from its coordinates,
# which usually means the graph has no coverage near that location.
MAX_LOCKER_SNAP_METERS = 200

MODE_DELIVERING = "delivering"
MODE_SEEKING_LOCKER = "seeking_locker"
MODE_STRANDED = "stranded"
