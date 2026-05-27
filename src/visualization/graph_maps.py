import folium

from src.agents.graph_rider import GraphRider
from src.agents.graph_locker import GraphLocker


def plot_graph_rider_snapshot(
    model,
    output_path="data/exports/graph_rider_snapshot.html"
):
    rider = next(
        agent for agent in model.agents
        if isinstance(agent, GraphRider)
    )

    graph = model.city_graph.graph

    # route coordinates
    route_coords = []
    for node in rider.route:
        x, y = model.city_graph.node_coordinates(node)
        route_coords.append((y, x))

    # current rider position
    current_x, current_y = model.city_graph.node_coordinates(rider.current_node)

    m = folium.Map(
        location=[current_y, current_x],
        zoom_start=14
    )

    # full route
    folium.PolyLine(
        route_coords,
        weight=4,
        opacity=0.7,
        popup="Rider route",
    ).add_to(m)

    # origin
    origin_x, origin_y = model.city_graph.node_coordinates(rider.route[0])
    folium.Marker(
        location=[origin_y, origin_x],
        popup="Origin",
        icon=folium.Icon(color="green")
    ).add_to(m)

    # destination
    dest_x, dest_y = model.city_graph.node_coordinates(rider.trip_destination_node)
    folium.Marker(
        location=[dest_y, dest_x],
        popup="Destination",
        icon=folium.Icon(color="red")
    ).add_to(m)

    # current rider location
    folium.Marker(
        location=[current_y, current_x],
        popup=f"Rider {rider.rider_id} | Battery: {rider.battery_level:.1f}",
        icon=folium.Icon(color="blue")
    ).add_to(m)

    # Plot graph lockers
    for agent in model.agents:
        if isinstance(agent, GraphLocker):
            locker_x, locker_y = model.city_graph.node_coordinates(agent.node_id)

            folium.Marker(
                location=[locker_y, locker_x],
                popup=(
                    f"Locker {agent.locker_id}<br>"
                    f"Charged: {agent.charged_batteries}<br>"
                    f"Depleted: {agent.depleted_batteries}"
                ),
                icon=folium.Icon(color="purple", icon="bolt", prefix="fa")
            ).add_to(m)

    m.save(output_path)
    print(f"Saved graph rider snapshot to {output_path}")