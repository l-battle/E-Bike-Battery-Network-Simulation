from mesa import Model
import random

from src.environment.city_graph import CityGraph
from src.agents.graph_rider import GraphRider
from src.agents.graph_locker import GraphLocker

from src.agents.graph_locker import GraphLocker
import networkx as nx

class GraphBatterySwapModel(Model):
    def __init__(self, place_name="Amsterdam, Netherlands"):
        super().__init__()

        self.city_graph = CityGraph(place_name, network_type='bike')
        self.current_step = 0

        nodes = list(self.city_graph.graph.nodes)
        self.graph_lockers = []

        self.swap_count = 0
        self.failed_swaps = 0       

        for i in range(3):
            locker_node = random.choice(nodes)

            locker = GraphLocker(
                self,
                locker_id=i,
                node_id=locker_node,
                charged_batteries=5,
                charge_time=10,
            )

            self.graph_lockers.append(locker)
            self.agents.add(locker)

        origin = random.choice(nodes)
        destination = random.choice(nodes)

        rider = GraphRider(
            self,
            rider_id=0,
            current_node=origin,
            destination_node=destination,
        )

        self.agents.add(rider)

    def step(self):
        self.current_step += 1
        self.agents.do("step")

    def nearest_available_locker(self, current_node):
        best_locker = None
        best_distance = float("inf")

        for agent in self.agents:
            if isinstance(agent, GraphLocker):

                # skip empty lockers
                if agent.charged_batteries <= 0:
                    continue

                try:
                    distance = nx.shortest_path_length(
                        self.city_graph.graph,
                        current_node,
                        agent.node_id,
                        weight="length",
                    )

                    if distance < best_distance:
                        best_distance = distance
                        best_locker = agent

                except nx.NetworkXNoPath:
                    continue

        return best_locker