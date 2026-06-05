import math

import osmnx as ox
import networkx as nx
import random

class CityGraph:
    def __init__(self, place_name, network_type='bike'):
        self.place_name = place_name
        self.network_type = network_type
        self.graph = self._load_graph()

    def _load_graph(self):
        ox.settings.use_cache = True
        ox.settings.log_console = True

        graph = ox.graph_from_place(
            self.place_name,
            network_type=self.network_type,
            simplify=True
        )

        # Restrict to the largest strongly connected component so that every
        # node can reach every other node. The directed bike network contains
        # dead-end sinks/sources; without this, riders can arrive at a node
        # from which no destination is reachable and pathfinding fails.
        largest_scc = max(nx.strongly_connected_components(graph), key=len)
        graph = graph.subgraph(largest_scc).copy()

        return graph
        
    def nearest_node(self, x, y):
        """Return the graph node closest to longitude x, latitude y.

        Uses an equirectangular approximation (good for city scale) so it
        works on the unprojected lat/lon graph without extra dependencies.
        """
        lon0 = math.radians(x)
        lat0 = math.radians(y)
        cos_lat0 = math.cos(lat0)

        best_node = None
        best_sq_dist = float("inf")

        for node, data in self.graph.nodes(data=True):
            dlon = math.radians(data["x"]) - lon0
            dlat = math.radians(data["y"]) - lat0
            sq_dist = (dlon * cos_lat0) ** 2 + dlat ** 2

            if sq_dist < best_sq_dist:
                best_sq_dist = sq_dist
                best_node = node

        return best_node
        
    def shortest_path(self, origin_node, destination_node):
        # Route by travel time -> the fastest path, not merely the shortest.
        return nx.shortest_path(
            self.graph,
            origin_node,
            destination_node,
            weight='travel_time'
        )

    def annotate_travel_costs(self, speed_kmh, consumption_rate):
        """Give every edge a travel_time (seconds) and battery_cost.

        Normal edges derive both from their length: travel_time = length /
        speed, battery_cost = length * consumption_rate. Special edges (e.g.
        ferries) set their own values and are left untouched.
        """
        metres_per_second = speed_kmh * 1000 / 3600

        for _, _, data in self.graph.edges(data=True):
            if data.get("is_ferry"):
                continue
            length = data.get("length", 0.0)
            data["travel_time"] = length / metres_per_second
            data["battery_cost"] = length * consumption_rate

    def edge_cost(self, u, v):
        """(travel_time, battery_cost, is_ferry) for the fastest edge u->v.

        Picks the parallel edge with the smallest travel_time, matching how
        shortest_path chooses among parallel edges.
        """
        edge_data = self.graph.get_edge_data(u, v)
        if not edge_data:
            return 0.0, 0.0, False
        best = min(
            edge_data.values(),
            key=lambda d: d.get("travel_time", float("inf")),
        )
        return (
            best.get("travel_time", 0.0),
            best.get("battery_cost", 0.0),
            bool(best.get("is_ferry", False)),
        )

    def add_ferry_routes(self, records):
        """Add ferry crossings as bidirectional edges.

        Each record needs from/to lat-lon, plus crossing and wait seconds.
        Ferry edges consume no battery and their travel_time is the crossing
        time plus the average wait. Endpoints snap to the nearest graph nodes.
        """
        for record in records:
            from_node = self.nearest_node(x=record["from_lon"], y=record["from_lat"])
            to_node = self.nearest_node(x=record["to_lon"], y=record["to_lat"])

            travel_time = record["crossing_seconds"] + record["wait_seconds"]
            length = self.distance_to_node(
                to_node, x=record["from_lon"], y=record["from_lat"]
            )

            for a, b in ((from_node, to_node), (to_node, from_node)):
                self.graph.add_edge(
                    a, b,
                    length=length,
                    travel_time=travel_time,
                    battery_cost=0.0,
                    is_ferry=True,
                    name=record.get("name", "ferry"),
                )
        
    def node_coordinates(self, node):
        data = self.graph.nodes[node]
        return data['x'], data['y']

    def distance_to_node(self, node, x, y):
        """Great-circle distance in metres from (lon x, lat y) to a node."""
        node_x, node_y = self.node_coordinates(node)

        lat1, lat2 = math.radians(y), math.radians(node_y)
        dlat = lat2 - lat1
        dlon = math.radians(node_x - x)

        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        )
        earth_radius_m = 6_371_000
        return 2 * earth_radius_m * math.asin(math.sqrt(a))

    def has_path(self, origin_node, destination_node):
        return nx.has_path(self.graph, origin_node, destination_node)

    def random_reachable_destination(self, origin_node, max_attempts=100):
        """Pick a random node that is reachable from origin_node."""
        nodes = list(self.graph.nodes)

        for _ in range(max_attempts):
            destination = random.choice(nodes)

            if destination == origin_node:
                continue

            if nx.has_path(self.graph, origin_node, destination):
                return destination

        raise ValueError(
            f"Could not find a reachable destination from {origin_node}."
        )

    def random_reachable_node_pair(self, max_attempts=100):
        nodes = list(self.graph.nodes)

        for _ in range(max_attempts):
            origin = random.choice(nodes)
            destination = random.choice(nodes)

            if origin == destination:
                continue

            try:
                nx.shortest_path(
                    self.graph,
                    origin,
                    destination,
                    weight="length",
                )
                return origin, destination

            except nx.NetworkXNoPath:
                continue

        raise ValueError("Could not find reachable node pair.")