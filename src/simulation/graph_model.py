from mesa import Model
import random
import warnings
import networkx as nx

from src.environment.city_graph import CityGraph
from src.environment.locker_data import load_locker_records
from src.environment.ferry_data import load_ferry_records
from src.environment.demand import DemandModel
from src.environment.weather import Weather
from src.agents.graph_rider import GraphRider
from src.agents.graph_locker import GraphLocker
from src.utils.config import (
    BATTERY_CAPACITY_WH, BATTERY_THRESHOLD_WH, CONSUMPTION_WH_PER_KM,
    DEFAULT_SPEED_KMH, TIME_STEP_SECONDS, DEFAULT_CHARGE_SECONDS,
    DEFAULT_CHARGED_BATTERIES, DEFAULT_LOCKER_CAPACITY,
    MAX_LOCKER_SNAP_METERS, DEFAULT_WEATHER,
    MODE_DELIVERING, MODE_SEEKING_LOCKER, MODE_STRANDED,
)

class GraphBatterySwapModel(Model):
    def __init__(
        self,
        place_name="Amsterdam, Netherlands",
        n_riders=10,
        n_lockers=5,
        locker_nodes=None,
        locker_csv=None,
        hotspot_csv=None,
        ferry_csv=None,
        weather=DEFAULT_WEATHER,
        seconds_per_step=TIME_STEP_SECONDS,
        rider_speed_kmh=DEFAULT_SPEED_KMH,
        city_graph=None,
    ):
        super().__init__()

        # A prebuilt CityGraph can be injected (tests, or to reuse one loaded
        # graph across many runs); otherwise it is built from place_name.
        self.city_graph = (
            city_graph if city_graph is not None
            else CityGraph(place_name, network_type='bike')
        )
        self.current_step = 0
        self.seconds_per_step = seconds_per_step
        self.rider_speed_kmh = rider_speed_kmh
        self.weather = Weather(weather)

        # Give every edge a travel_time and battery_cost (routing uses the
        # fastest path). Ferries are added afterwards with their own costs.
        self.city_graph.annotate_travel_costs(rider_speed_kmh, CONSUMPTION_WH_PER_KM)
        if ferry_csv is not None:
            self.city_graph.add_ferry_routes(load_ferry_records(ferry_csv))

        # Demand model (None = uniform random spawn/destinations)
        self.demand = None
        if hotspot_csv is not None:
            demand = DemandModel(self.city_graph, hotspot_csv)
            if demand.is_active:
                self.demand = demand
            else:
                warnings.warn(
                    "Hotspot CSV produced no usable hotspots; falling back to "
                    "uniform random spawn and destinations.",
                    stacklevel=2,
                )

        self.graph_lockers = []

        self.swap_count = 0
        self.failed_swaps = 0
        self.completed_trips = 0
        self.stranded_count = 0

        self.history = []

        if locker_nodes is not None:
            self._create_lockers_from_nodes(locker_nodes)
        elif locker_csv is not None:
            self._create_lockers_from_csv(locker_csv)
        else:
            self._create_random_lockers(n_lockers)

        for i in range(n_riders):
            origin, destination = self._spawn_node_pair()
            rider = GraphRider(
                self,
                rider_id=i,
                current_node=origin,
                destination_node=destination,
                battery_level=BATTERY_CAPACITY_WH,
                battery_threshold=BATTERY_THRESHOLD_WH,
            )

            self.agents.add(rider)

    def sample_destination(self, current_node):
        """Pick a delivery destination, demand-weighted if a demand model is
        configured, otherwise a uniformly random reachable node."""
        if self.demand is not None:
            return self.demand.sample_node(exclude=current_node)
        return self.city_graph.random_reachable_destination(current_node)

    def _spawn_node_pair(self):
        """Origin/destination pair for a new rider, demand-weighted if set."""
        if self.demand is not None:
            origin = self.demand.sample_node()
            destination = self.demand.sample_node(exclude=origin)
            return origin, destination
        return self.city_graph.random_reachable_node_pair()

    def _add_locker(self, locker_id, node_id, charged_batteries, capacity):
        locker = GraphLocker(
            self,
            locker_id=locker_id,
            node_id=node_id,
            charged_batteries=charged_batteries,
            capacity=capacity,
            charge_seconds=DEFAULT_CHARGE_SECONDS,
        )
        self.graph_lockers.append(locker)
        self.agents.add(locker)

    def _create_lockers_from_nodes(self, locker_nodes):
        """Place lockers at an explicit set of graph nodes (a sampled layout)."""
        for i, node in enumerate(locker_nodes):
            self._add_locker(
                i, node,
                charged_batteries=DEFAULT_CHARGED_BATTERIES,
                capacity=DEFAULT_LOCKER_CAPACITY,
            )

    def _create_random_lockers(self, n_lockers):
        nodes = list(self.city_graph.graph.nodes)
        for i in range(n_lockers):
            self._add_locker(
                i,
                random.choice(nodes),
                charged_batteries=DEFAULT_CHARGED_BATTERIES,
                capacity=DEFAULT_LOCKER_CAPACITY,
            )

    def _create_lockers_from_csv(self, csv_path):
        records = load_locker_records(csv_path)
        for record in records:
            # Snap the real lat/lon to the nearest graph node.
            node_id = self.city_graph.nearest_node(x=record["lon"], y=record["lat"])

            snap_distance = self.city_graph.distance_to_node(
                node_id, x=record["lon"], y=record["lat"]
            )
            if snap_distance > MAX_LOCKER_SNAP_METERS:
                warnings.warn(
                    f"Locker {record['locker_id']} ('{record['name']}') snapped "
                    f"{snap_distance:.0f} m from its coordinates "
                    f"(> {MAX_LOCKER_SNAP_METERS} m). The graph likely has no "
                    f"coverage near this location.",
                    stacklevel=2,
                )

            self._add_locker(
                record["locker_id"],
                node_id,
                charged_batteries=record["charged_batteries"],
                capacity=record["capacity"],
            )

    def step(self):
        self.current_step += 1
        self.agents.do("step")

        self.record_history()

    def nearest_available_locker(self, current_node):
        best_locker = None
        best_time = float("inf")

        for agent in self.agents:
            if isinstance(agent, GraphLocker):

                # skip empty lockers
                if agent.charged_batteries <= 0:
                    continue

                try:
                    travel_time = nx.shortest_path_length(
                        self.city_graph.graph,
                        current_node,
                        agent.node_id,
                        weight="travel_time",
                    )

                    if travel_time < best_time:
                        best_time = travel_time
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
            "weather": self.weather.condition,
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