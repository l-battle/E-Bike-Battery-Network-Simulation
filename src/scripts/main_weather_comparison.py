"""Run the simulation under each weather condition and compare outcomes."""
import matplotlib.pyplot as plt

from src.simulation.graph_model import GraphBatterySwapModel
from src.utils.config import WEATHER_PRESETS
from src.visualization.graph_plots import plot_weather_comparison

N_RIDERS = 15
STEPS = 1500

results = {}
for weather in WEATHER_PRESETS:
    model = GraphBatterySwapModel(
        n_riders=N_RIDERS,
        locker_csv="data/lockers_amsterdam.csv",
        hotspot_csv="data/hotspots_amsterdam.csv",
        ferry_csv="data/ferries_amsterdam.csv",
        weather=weather,
    )
    for _ in range(STEPS):
        model.step()

    results[weather] = model.history[-1]
    print(
        f"{weather:6s} -> trips={results[weather]['completed_trips']:4d} "
        f"swaps={results[weather]['swap_count']:4d} "
        f"stranded={results[weather]['stranded_count']:3d} "
        f"avg_batt={results[weather]['avg_battery']:.1f}"
    )

plot_weather_comparison(results)
plt.show()
