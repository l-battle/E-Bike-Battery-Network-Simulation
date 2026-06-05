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

        #graph = ox.project_graph(graph)
        return graph
        
    def nearest_node(self, x, y):
        return ox.distance.nearest_nodes(self.graph, X=x, Y=y)
        
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

    def edge_length(self, u, v):
        """Length in metres of the edge between u and v.

        OSM graphs are multigraphs, so parallel edges can exist; we take the
        shortest, matching how shortest_path weights edges by 'length'.
        """
        edge_data = self.graph.get_edge_data(u, v)
        if not edge_data:
            return 0.0
        return min(d.get("length", 0.0) for d in edge_data.values())
        
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