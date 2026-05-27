from mesa import Agent
from src.utils.config import MODE_ARRIVED, MODE_DELIVERING, MODE_SEEKING_LOCKER, MODE_STRANDED, DEFAULT_BATTERY_THRESHOLD, DEFAULT_BATTERY_LEVEL, DEFAULT_CONSUMPTION

class GraphRider(Agent):
    def __init__(self, 
                 model, 
                 rider_id, 
                 current_node, 
                 destination_node, 
                 battery_level=DEFAULT_BATTERY_LEVEL, 
                 battery_threshold=DEFAULT_BATTERY_THRESHOLD,
                 consumption_rate=DEFAULT_CONSUMPTION):
        super().__init__(model)

        self.rider_id = rider_id
        self.current_node = current_node
        self.trip_destination_node = destination_node

        self.battery_level = battery_level
        self.battery_threshold = battery_threshold
        self.consumption_rate = consumption_rate

        self.route = self.model.city_graph.shortest_path(
            self.current_node,
            self.trip_destination_node
        )

        self.trip_destination_node
        self.target_locker = None
        self.mode = MODE_DELIVERING

        self.route = self.model.city_graph.shortest_path(
            self.current_node,
            self.trip_destination_node,
        )

        self.route_index = 0

    def step(self):
        if self.mode in [MODE_ARRIVED, MODE_STRANDED]:
            return
        # If trip is completed
        if self.route_index >= len(self.route) - 1:
            if self.mode == MODE_SEEKING_LOCKER:
                self.try_swap()
            else:
                self.mode = MODE_ARRIVED
                self.model.completed_trips += 1
            return

        # If battery is low while delivering, reroute to nearest locker
        if (
            self.battery_level <= self.battery_threshold
            and self.mode == MODE_DELIVERING
        ):
            nearest_locker = self.model.nearest_available_locker(self.current_node)

            if nearest_locker is None:
                self.mode = MODE_STRANDED
                return

            self.target_locker = nearest_locker
            self.mode = MODE_SEEKING_LOCKER

            self.route = self.model.city_graph.shortest_path(
                self.current_node,
                self.target_locker.node_id,
            )
            self.route_index = 0

        # Move one node along current route
        current = self.route[self.route_index]
        next_node = self.route[self.route_index + 1]

        edge_data = self.model.city_graph.graph.get_edge_data(current, next_node)

        first_edge = list(edge_data.values())[0]
        distance = first_edge.get("length", 0)

        self.battery_level -= distance * self.consumption_rate

        if self.battery_level <= 0:
            self.battery_level = 0
            self.mode = MODE_STRANDED
            self.model.failed_swaps += 1
            self.model.stranded_count += 1
            return

        self.route_index += 1
        self.current_node = next_node

    def try_swap(self):
        if self.target_locker is None:
            self.mode = MODE_STRANDED
            self.model.failed_swaps += 1
            return

        if self.target_locker.charged_batteries <= 0:
            self.mode = MODE_STRANDED
            self.model.failed_swaps += 1
            return

        self.model.swap_count += 1
        self.target_locker.charged_batteries -= 1
        self.target_locker.add_depleted_battery()

        self.battery_level = 100
        self.target_locker = None
        self.mode = MODE_DELIVERING

        self.route = self.model.city_graph.shortest_path(
            self.current_node,
            self.trip_destination_node,
        )
        self.route_index = 0

