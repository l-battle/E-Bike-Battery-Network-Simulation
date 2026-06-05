DEFAULT_BATTERY_LEVEL = 100
DEFAULT_BATTERY_THRESHOLD = 20
DEFAULT_CONSUMPTION = 0.005

# Time / speed model
TIME_STEP_SECONDS = 10      # simulated seconds elapsed per model step
DEFAULT_SPEED_KMH = 18      # rider cruising speed (e-bike)

DEFAULT_CHARGE_TIME = 10

# Warn if a CSV locker snaps further than this (metres) from its coordinates,
# which usually means the graph has no coverage near that location.
MAX_LOCKER_SNAP_METERS = 200

DEFAULT_RIDER_COUNT = 5
DEFAULT_LOCKER_COUNT = 3

MODE_DELIVERING = "delivering"
MODE_SEEKING_LOCKER = "seeking_locker"
MODE_ARRIVED = "arrived"
MODE_STRANDED = "stranded"
