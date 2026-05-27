from src.environment.city_graph import CityGraph
from src.visualization.maps import plot_city_graph_sample

city = CityGraph("Amsterdam, Netherlands", network_type='bike')

plot_city_graph_sample(city)