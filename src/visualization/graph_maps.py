import folium
from folium.plugins import HeatMap

from src.agents.graph_rider import GraphRider
from src.agents.graph_locker import GraphLocker


def add_hotspot_layer(m, model):
    """Add a toggleable demand heatmap + centre markers from the demand model.

    Renders the actual demand surface the simulation samples from: every zone
    node, weighted by its Gaussian falloff times the hotspot's demand weight.
    """
    if getattr(model, "demand", None) is None:
        return

    heat_data = []
    centers = folium.FeatureGroup(name="Hotspot centres", show=True)

    for hotspot in model.demand.hotspots:
        for node, node_weight in zip(hotspot["zone_nodes"], hotspot["zone_weights"]):
            x, y = model.city_graph.node_coordinates(node)
            heat_data.append([y, x, node_weight * hotspot["weight"]])

        # A labelled marker at the (weighted) centre of the zone
        cx = sum(model.city_graph.node_coordinates(n)[0] for n in hotspot["zone_nodes"]) / len(hotspot["zone_nodes"])
        cy = sum(model.city_graph.node_coordinates(n)[1] for n in hotspot["zone_nodes"]) / len(hotspot["zone_nodes"])
        folium.CircleMarker(
            location=[cy, cx],
            radius=6,
            color="orange",
            fill=True,
            fill_opacity=0.8,
            popup=f"{hotspot['name']} (weight {hotspot['weight']})",
        ).add_to(centers)

    heat_layer = folium.FeatureGroup(name="Demand heatmap", show=True)
    HeatMap(heat_data, radius=18, blur=22, min_opacity=0.3).add_to(heat_layer)

    heat_layer.add_to(m)
    centers.add_to(m)


def plot_graph_rider_snapshot(
    model,
    output_path="data/exports/graph_rider_snapshot.html"
):
    riders = [
        agent for agent in model.agents
        if isinstance(agent, GraphRider)
    ]

    if not riders:
        print("No riders found.")
        return

    # Center map on first rider
    first_rider = riders[0]
    center_x, center_y = model.city_graph.node_coordinates(first_rider.current_node)

    m = folium.Map(
        location=[center_y, center_x],
        zoom_start=13
    )

    # Plot each rider
    for rider in riders:
        # Current active route
        route_coords = []
        for node in rider.route:
            x, y = model.city_graph.node_coordinates(node)
            route_coords.append((y, x))

        folium.PolyLine(
            route_coords,
            weight=3,
            opacity=0.5,
            popup=f"Rider {rider.rider_id} route",
        ).add_to(m)

        # Origin/current route start
        origin_x, origin_y = model.city_graph.node_coordinates(rider.route[0])
        folium.Marker(
            location=[origin_y, origin_x],
            popup=f"Rider {rider.rider_id} route start",
            icon=folium.Icon(color="green")
        ).add_to(m)

        # Trip destination
        dest_x, dest_y = model.city_graph.node_coordinates(rider.trip_destination_node)
        folium.Marker(
            location=[dest_y, dest_x],
            popup=f"Rider {rider.rider_id} destination",
            icon=folium.Icon(color="red")
        ).add_to(m)

        # Current rider location
        current_x, current_y = model.city_graph.node_coordinates(rider.current_node)
        folium.Marker(
            location=[current_y, current_x],
            popup=(
                f"Rider {rider.rider_id}<br>"
                f"Battery: {rider.battery_level:.1f}<br>"
                f"Mode: {rider.mode}"
            ),
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

    # Demand hotspots overlay (only if a demand model is configured)
    add_hotspot_layer(m, model)

    folium.LayerControl(collapsed=False).add_to(m)

    m.save(output_path)
    print(f"Saved graph rider snapshot to {output_path}")