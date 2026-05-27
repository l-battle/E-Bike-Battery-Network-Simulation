import folium

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