from src.simulation.graph_model import GraphBatterySwapModel
from src.visualization.graph_maps import plot_graph_rider_snapshot

model = GraphBatterySwapModel()

for _ in range(50):
    model.step()

plot_graph_rider_snapshot(model)