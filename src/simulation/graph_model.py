from mesa import Model
import random
import networkx as nx

from src.environment.city_graph import CityGraph
from src.agents.graph_rider import GraphRider
from src.agents.graph_locker import GraphLocker
from src.utils.config import (
    DEFAULT_BATTERY_LEVEL, DEFAULT_BATTERY_THRESHOLD, DEFAULT_CONSUMPTION,
    DEFAULT_SPEED_KMH, TIME_STEP_SECONDS,
    MODE_DELIVERING, MODE_SEEKING_LOCKER, MODE_ARRIVED, MODE_STRANDED,
)

class GraphBatterySwapModel(Model):
    def __init__(
        self,
        place_name="Amsterdam, Netherlands",
        n_riders=10,
        n_lockers=5,
        seconds_per_step=TIME_STEP_SECONDS,
        rider_speed_kmh=DEFAULT_SPEED_KMH,
    ):
        super().__init__()

        self.city_graph = CityGraph(place_name, network_type='bike')
        self.current_step = 0
        self.seconds_per_step = seconds_per_step
        self.rider_speed_kmh = rider_speed_kmh

        nodes = list(self.city_graph.graph.nodes)
        self.graph_lockers = []

        self.swap_count = 0
        self.failed_swaps = 0
        self.completed_trips = 0
        self.stranded_count = 0

        self.history = []       

        for i in range(n_lockers):
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

        origin, destination = self.city_graph.random_reachable_node_pair()

        for i in range(n_riders):
            origin, destination = self.city_graph.random_reachable_node_pair()
            rider = GraphRider(
                self,
                rider_id=i,
                current_node=origin,
                destination_node=destination,
                battery_level=DEFAULT_BATTERY_LEVEL,
                battery_threshold=DEFAULT_BATTERY_THRESHOLD,
                consumption_rate=DEFAULT_CONSUMPTION,
                speed_kmh=self.rider_speed_kmh,
            )

            self.agents.add(rider)

    def step(self):
        self.current_step += 1
        self.agents.do("step")

        self.record_history()

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
    
    def record_history(self):
        riders = [
            agent for agent in self.agents
            if isinstance(agent, GraphRider)
        ]

        lockers = [
            agent for agent in self.agents
            if isinstance(agent, GraphLocker)
        ]

        avg_battery = (
            sum(rider.battery_level for rider in riders) / len(riders)
            if riders else 0
        )

        active_riders = sum(
            rider.mode == MODE_DELIVERING
            for rider in riders
        )

        seeking_riders = sum(
            rider.mode == MODE_SEEKING_LOCKER
            for rider in riders
        )

        stranded_riders = sum(
            rider.mode == MODE_STRANDED
            for rider in riders
        )

        total_charged = sum(
            locker.charged_batteries
            for locker in lockers
        )

        total_depleted = sum(
            locker.depleted_batteries
            for locker in lockers
        )

        locker_states = {}

        for locker in lockers:
            locker_states[f"locker_{locker.locker_id}_charged"] = locker.charged_batteries
            locker_states[f"locker_{locker.locker_id}_depleted"] = locker.depleted_batteries

        self.history.append({
            "step": self.current_step,
            "elapsed_minutes": self.current_step * self.seconds_per_step / 60,
            "swap_count": self.swap_count,
            "failed_swaps": self.failed_swaps,
            "completed_trips": self.completed_trips,
            "stranded_count": self.stranded_count,
            "avg_battery": avg_battery,
            "active_riders": active_riders,
            "seeking_riders": seeking_riders,
            "stranded_riders": stranded_riders,
            "total_charged_batteries": total_charged,
            "total_depleted_batteries": total_depleted,
            **locker_states,
        })