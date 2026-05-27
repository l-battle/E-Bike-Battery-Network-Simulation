from src.environment.city_graph import CityGraph

city = CityGraph("Amsterdam, Netherlands", network_type='bike')

print("graph Loaded")
print("nodes:", len(city.graph.nodes))
print("edges:", len(city.graph.edges))

some_node = list(city.graph.nodes)[0]
print("example node:", some_node)
print("coords:", city.node_coordinates(some_node))