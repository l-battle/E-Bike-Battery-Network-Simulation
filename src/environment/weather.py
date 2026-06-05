from src.utils.config import WEATHER_PRESETS, DEFAULT_WEATHER


class Weather:
    """Global weather condition affecting riding speed and battery drain.

    Exposes two multipliers applied at edge traversal time:
      - travel_time_factor: >1 means slower riding (rain, snow, congestion)
      - battery_factor:      >1 means more battery drain (cold, headwind)

    Factors are global, so they do not change which route is fastest; routing
    is unaffected and edges need no re-annotation.
    """

    def __init__(self, condition=DEFAULT_WEATHER):
        if condition not in WEATHER_PRESETS:
            raise ValueError(
                f"Unknown weather '{condition}'. "
                f"Options: {sorted(WEATHER_PRESETS)}"
            )

        preset = WEATHER_PRESETS[condition]
        self.condition = condition
        self.travel_time_factor = preset["travel_time_factor"]
        self.battery_factor = preset["battery_factor"]

    def __repr__(self):
        return (
            f"Weather({self.condition!r}, "
            f"travel_time_factor={self.travel_time_factor}, "
            f"battery_factor={self.battery_factor})"
        )
