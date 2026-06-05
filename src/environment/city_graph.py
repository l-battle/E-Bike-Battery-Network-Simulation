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
        return nx.shortest_path(
            self.graph, 
            origin_node,
            destination_node,
            weight='length'
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

    def edge_length(self, u, v):
        """Length in metres of the edge between u and v.

        OSM graphs are multigraphs, so parallel edges can exist; we take the
        shortest, matching how shortest_path weights edges by 'length'.
        """
        edge_data = self.graph.get_edge_data(u, v)
        if not edge_data:
            return 0.0
        return min(d.get("length", 0.0) for d in edge_data.values())
        
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