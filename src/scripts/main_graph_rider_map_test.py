from src.simulation.graph_model import GraphBatterySwapModel
from src.visualization.graph_maps import plot_graph_rider_snapshot
from src.visualization.graph_plots import show_all_graph_metrics

model = GraphBatterySwapModel(
    n_riders=15,
    locker_csv="data/lockers_amsterdam.csv",
    hotspot_csv="data/hotspots_amsterdam.csv",
)

for _ in range(1000):
    model.step()

plot_graph_rider_snapshot(model)
show_all_graph_metrics(model)