DEFAULT_BATTERY_LEVEL = 100
DEFAULT_BATTERY_THRESHOLD = 20
DEFAULT_CONSUMPTION = 0.005

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
    "rain":  {"travel_time_factor": 1.25, "battery_factor": 1.15},
    "wind":  {"travel_time_factor": 1.10, "battery_factor": 1.25},
    "snow":  {"travel_time_factor": 1.60, "battery_factor": 1.35},
    "heat":  {"travel_time_factor": 1.05, "battery_factor": 1.10},
}

# Locker battery economy
DEFAULT_CHARGE_SECONDS = 3 * 3600     # time to recharge one depleted battery
DEFAULT_CHARGED_BATTERIES = 5         # charged batteries a locker starts with
DEFAULT_LOCKER_CAPACITY = 10          # max total batteries (charged + depleted)

# Warn if a CSV locker snaps further than this (metres) from its coordinates,
# which usually means the graph has no coverage near that location.
MAX_LOCKER_SNAP_METERS = 200

MODE_DELIVERING = "delivering"
MODE_SEEKING_LOCKER = "seeking_locker"
MODE_STRANDED = "stranded"
