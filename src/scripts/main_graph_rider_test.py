from src.simulation.graph_model import GraphBatterySwapModel
from src.agents.graph_rider import GraphRider

model = GraphBatterySwapModel()

for step in range(50):
    model.step()

    for agent in model.agents:
        if isinstance(agent, GraphRider):
            x, y = model.city_graph.node_coordinates(agent.current_node)

            print(
                f"Step {model.current_step} | "
                f"Node: {agent.current_node} | "
                f"Coords: ({x:.5f}, {y:.5f}) | "
                f"Battery: {agent.battery_level:.2f} | "
                f"Status: {agent.mode}"
            )