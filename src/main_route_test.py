from src.environment.city_graph import CityGraph
from src.visualization.maps import plot_random_route

city = CityGraph(
    "Amsterdam, Netherlands",
    network_type="bike"
)

plot_random_route(city)