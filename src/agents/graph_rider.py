from mesa import Agent
from src.utils.config import (
    MODE_DELIVERING,
    MODE_SEEKING_LOCKER,
    MODE_STRANDED,
    BATTERY_CAPACITY_WH,
    BATTERY_THRESHOLD_WH,
)


class GraphRider(Agent):
    def __init__(
        self,
        model,
        rider_id,
        current_node,
        destination_node,
        battery_level=BATTERY_CAPACITY_WH,
        battery_threshold=BATTERY_THRESHOLD_WH,
    ):
        super().__init__(model)

        self.rider_id = rider_id
        self.current_node = current_node
        self.trip_destination_node = destination_node

        self.battery_level = battery_level
        self.battery_threshold = battery_threshold

        self.target_locker = None
        self.mode = MODE_DELIVERING

        # Seconds already spent on the edge from the current node toward the
        # next node in the route. Lets a rider stop partway along an edge.
        self.time_into_edge = 0.0

        self.set_route(self.trip_destination_node)

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

        # Advance along the route using this step's time budget
        self._advance(self.model.seconds_per_step)

    def _advance(self, time_budget):
        """Travel for `time_budget` seconds along the route, spanning edges.

        Battery is drained in proportion to the fraction of each edge covered,
        so partial traversals (and zero-battery-cost ferry edges) are handled.
        """
        remaining = time_budget

        while remaining > 1e-9 and self.route_index < len(self.route) - 1:
            current = self.route[self.route_index]
            next_node = self.route[self.route_index + 1]

            travel_time, battery_cost, is_ferry = self.model.city_graph.edge_cost(
                current, next_node
            )

            # Weather slows riding and drains more battery, but ferries run on
            # schedule and consume no battery, so they are left unaffected.
            if not is_ferry:
                travel_time *= self.model.weather.travel_time_factor
                battery_cost *= self.model.weather.battery_factor

            edge_remaining = travel_time - self.time_into_edge

            step_time = min(remaining, edge_remaining)
            fraction = step_time / travel_time if travel_time > 0 else 1.0

            self.battery_level -= fraction * battery_cost

            if self.battery_level <= 0:
                self.battery_level = 0
                self.mode = MODE_STRANDED
                self.model.failed_swaps += 1
                self.model.stranded_count += 1
                return

            self.time_into_edge += step_time
            remaining -= step_time

            # Reached the next node
            if self.time_into_edge >= travel_time - 1e-9:
                self.route_index += 1
                self.current_node = next_node
                self.time_into_edge = 0.0

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

        self.battery_level = BATTERY_CAPACITY_WH
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
        self.time_into_edge = 0.0
