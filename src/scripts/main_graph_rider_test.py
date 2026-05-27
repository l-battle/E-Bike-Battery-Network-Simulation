from src.simulation.graph_model import GraphBatterySwapModel
from src.agents.graph_rider import GraphRider

model = GraphBatterySwapModel(n_riders=10, n_lockers=5)

for step in range(80):
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

print(model.history[-1])