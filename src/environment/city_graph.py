import osmnx as ox
import networkx as nx

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
        
