from src.simulation.graph_model import GraphBatterySwapModel
from src.visualization.graph_maps import plot_graph_rider_snapshot
from src.visualization.graph_plots import show_all_graph_metrics

model = GraphBatterySwapModel()

for _ in range(1000):
    model.step()

plot_graph_rider_snapshot(model)
show_all_graph_metrics(model)