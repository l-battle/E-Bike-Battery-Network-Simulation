from dataclasses import dataclass, asdict, replace

from src.utils.config import DEFAULT_SPEED_KMH, TIME_STEP_SECONDS


@dataclass(frozen=True)
class ExperimentConfig:
    """All parameters for a single simulation run.

    Frozen so configs are hashable and safe to reuse; use `with_overrides`
    (dataclasses.replace) to derive variants.
    """

    name: str = "exp"

    # World
    place_name: str = "Amsterdam, Netherlands"
    locker_csv: str = "data/lockers_amsterdam.csv"
    hotspot_csv: str = "data/hotspots_amsterdam.csv"
    ferry_csv: str = "data/ferries_amsterdam.csv"
    n_lockers: int = 5            # only used when locker_csv is None

    # Scenario conditions (sampled across runs)
    n_riders: int = 15
    weather: str = "clear"

    # Physics / numerics
    rider_speed_kmh: float = DEFAULT_SPEED_KMH
    seconds_per_step: int = TIME_STEP_SECONDS

    # Run control
    n_steps: int = 2000
    warmup_steps: int = 500       # discarded before measuring steady state
    seed: int = 0

    def with_overrides(self, **changes):
        return replace(self, **changes)

    def to_dict(self):
        return asdict(self)
