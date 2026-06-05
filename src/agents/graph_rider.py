from mesa import Agent
from src.utils.config import (
    MODE_DELIVERING,
    MODE_SEEKING_LOCKER,
    MODE_STRANDED,
    DEFAULT_BATTERY_THRESHOLD,
    DEFAULT_BATTERY_LEVEL,
    DEFAULT_CONSUMPTION,
    DEFAULT_SPEED_KMH,
)


class GraphRider(Agent):
    def __init__(
        self,
        model,
        rider_id,
        current_node,
        destination_node,
        battery_level=DEFAULT_BATTERY_LEVEL,
        battery_threshold=DEFAULT_BATTERY_THRESHOLD,
        consumption_rate=DEFAULT_CONSUMPTION,
        speed_kmh=DEFAULT_SPEED_KMH,
    ):
        super().__init__(model)

        self.rider_id = rider_id
        self.current_node = current_node
        self.trip_destination_node = destination_node

        self.battery_level = battery_level
        self.battery_threshold = battery_threshold
        self.consumption_rate = consumption_rate
        self.speed_kmh = speed_kmh

        self.target_locker = None
        self.mode = MODE_DELIVERING

        # Metres already travelled along the edge from the current node toward
        # the next node in the route. Lets a rider stop partway down an edge.
        self.dist_into_edge = 0.0

        self.set_route(self.trip_destination_node)

    def distance_per_step(self):
        """Metres the rider can travel in one model step at its speed."""
        metres_per_second = self.speed_kmh * 1000 / 3600
        return metres_per_second * self.model.seconds_per_step

    def step(self):
        if self.mode == MODE_STRANDED:
            return

        # Reached the end of the current route
        if self.route_index >= len(self.route) - 1:
            if self.mode == MODE_SEEKING_LOCKER:
                self.try_swap()
            elif self.mode == MODE_DELIVERING:
                self.complete_delivery()
            return

        # If battery is low while delivering, reroute to nearest locker
        if (
            self.battery_level <= self.battery_threshold
            and self.mode == MODE_DELIVERING
        ):
            nearest_locker = self.model.nearest_available_locker(self.current_node)

            if nearest_locker is None:
                self.mode = MODE_STRANDED
                self.model.stranded_count += 1
                return

            self.target_locker = nearest_locker
            self.mode = MODE_SEEKING_LOCKER
            self.set_route(self.target_locker.node_id)

        # Move along the route by this step's travel distance
        self._advance(self.distance_per_step())

    def _advance(self, distance):
        """Travel `distance` metres along the route, spanning edges as needed."""
        remaining = distance

        while remaining > 1e-9 and self.route_index < len(self.route) - 1:
            current = self.route[self.route_index]
            next_node = self.route[self.route_index + 1]

            edge_length = self.model.city_graph.edge_length(current, next_node)
            edge_remaining = edge_length - self.dist_into_edge

            travel = min(remaining, edge_remaining)

            self.battery_level -= travel * self.consumption_rate

            if self.battery_level <= 0:
                self.battery_level = 0
                self.mode = MODE_STRANDED
                self.model.failed_swaps += 1
                self.model.stranded_count += 1
                return

            self.dist_into_edge += travel
            remaining -= travel

            # Reached the next node
            if self.dist_into_edge >= edge_length - 1e-9:
                self.route_index += 1
                self.current_node = next_node
                self.dist_into_edge = 0.0

    def try_swap(self):
        if self.target_locker is None:
            self.mode = MODE_STRANDED
            self.model.stranded_count += 1
            self.model.failed_swaps += 1
            return

        if self.target_locker.charged_batteries <= 0:
            self.mode = MODE_STRANDED
            self.model.failed_swaps += 1
            self.model.stranded_count += 1
            return

        self.model.swap_count += 1
        self.target_locker.charged_batteries -= 1
        self.target_locker.add_depleted_battery()

        self.battery_level = DEFAULT_BATTERY_LEVEL
        self.target_locker = None
        self.mode = MODE_DELIVERING

        # There may be no path from this locker back to the original
        # destination; if so, pick a fresh reachable destination instead.
        if self.model.city_graph.has_path(
            self.current_node, self.trip_destination_node
        ):
            self.set_route(self.trip_destination_node)
        else:
            self.choose_new_destination()

    def choose_new_destination(self):
        self.trip_destination_node = self.model.sample_destination(self.current_node)
        self.set_route(self.trip_destination_node)
        self.mode = MODE_DELIVERING

    def complete_delivery(self):
        self.model.completed_trips += 1
        self.choose_new_destination()

    def set_route(self, destination_node):
        self.route = self.model.city_graph.shortest_path(
            self.current_node,
            destination_node,
        )
        self.route_index = 0
        self.dist_into_edge = 0.0
