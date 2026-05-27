import folium
import random

def plot_city_graph_sample(city_graph, output_path="data/exports/city_graph.html"):
    graph = city_graph.graph

    #get center
    nodes = list(graph.nodes(data=True))
    avg_x = sum(data['x'] for _, data in nodes) / len(nodes)
    avg_y = sum(data['y'] for _, data in nodes) / len(nodes)

    m = folium.Map(location=[avg_y, avg_x], zoom_start=13)

    #plot edges
    for u, v, data in list(graph.edges(data=True))[:1000]:
        x1, y1 = graph.nodes[u]['x'], graph.nodes[u]['y']
        x2, y2 = graph.nodes[v]['x'], graph.nodes[v]['y']

        folium.PolyLine(
            locations=[(x1, y1),(x2, y2)],
            weight=1,
            opacity=0.4,
        ).add_to(m)

    m.save(output_path)
    print(f"saved map to {output_path}")

def plot_random_route(city_graph, output_path="data/exports/random_route.html"):
    graph = city_graph.graph

    #2 random nodes
    nodes = list(graph.nodes)

    origin = random.choice(nodes)
    destination = random.choice(nodes)

    #shortest path
    route = city_graph.shortest_path(origin, destination)

    origin_x, origin_y = city_graph.node_coordinates(origin)

    m = folium.Map(
        location=[origin_y, origin_x],
        zoom_start=13
    )

    #route
    route_coordinates = []

    for node in route:
        x, y = city_graph.node_coordinates(node)
        route_coordinates.append((y, x))

    folium.PolyLine(
        route_coordinates,
        color='red',
        weight=4,
        opacity=0.9,
    ).add_to(m)

    #origin
    folium.Marker(
        location=[origin_y, origin_x],
        popup='origin',
        icon=folium.Icon(color='green'),
    ).add_to(m)

    #destination
    dest_x, dest_y = city_graph.node_coordinates(destination)

    folium.Marker(
        location=[dest_y, dest_x],
        popup='destination',
        icon=folium.Icon(color='red'),
    ).add_to(m)

    m.save(output_path)

    print(f"saved route map to {output_path}")