import networkx as nx
from collections import defaultdict

from src.utils.config import DEFAULT_LOCKER_CAPACITY


def _require_travel_time(city_graph):
    """Guard: Dijkstra silently treats a missing 'travel_time' as 1.0, so make
    sure the graph was annotated first."""
    for _, _, data in city_graph.graph.edges(data=True):
        if "travel_time" not in data:
            raise ValueError(
                "Graph has no 'travel_time'; call annotate_travel_costs() first."
            )
        return  # checking one edge is enough


def _safe_div(a, b):
    return a / b if b else 0.0


def compute_features(city_graph, demand, locker_nodes, scenario,
                     fixed_capacity=DEFAULT_LOCKER_CAPACITY,
                     coverage_minutes=(3, 5, 10), unmet_threshold_min=10):
    """Turn a layout + scenario into a flat feature dict."""
    _require_travel_time(city_graph)

    locker_nodes = list(locker_nodes)
    n_riders = scenario["n_riders"]
    n_lockers = len(locker_nodes)

    # --- scenario + supply ---
    features = {
        "n_riders": n_riders,
        "rider_speed_kmh": scenario["rider_speed_kmh"],
        "weather": scenario["weather"],
        "n_lockers": n_lockers,
        "total_capacity": n_lockers * fixed_capacity,
        "lockers_per_rider": _safe_div(n_lockers, n_riders),
        "capacity_per_rider": _safe_div(n_lockers * fixed_capacity, n_riders),
    }

    # --- demand points: node -> total weight ---
    weight = defaultdict(float)
    for hotspot in demand.hotspots:
        for node, w in zip(hotspot["zone_nodes"], hotspot["zone_weights"]):
            weight[node] += w * hotspot["weight"]
    total_demand = sum(weight.values())

    # --- distance from every node to its nearest locker (one Dijkstra) ---
    if locker_nodes:
        dist = nx.multi_source_dijkstra_path_length(
            city_graph.graph, set(locker_nodes), weight="travel_time"
        )
    else:
        dist = {}  # empty layout -> everything is "infinitely far"

    def d(node):
        return dist.get(node, float("inf"))

    # --- step 5: coverage + demand-distance ---
    for x in coverage_minutes:
        covered = sum(w for node, w in weight.items() if d(node) <= x * 60)
        features[f"coverage_{x}min"] = _safe_div(covered, total_demand)

    features["mean_demand_to_locker_min"] = _safe_div(
        sum(w * d(node) for node, w in weight.items()), total_demand
    ) / 60

    features["unmet_demand_frac"] = _safe_div(
        sum(w for node, w in weight.items() if d(node) > unmet_threshold_min * 60),
        total_demand,
    )

    # weighted 90th percentile of distance
    p90 = 0.0
    if total_demand > 0:
        ordered = sorted(weight, key=d)
        cum = 0.0
        for node in ordered:
            cum += weight[node]
            if cum >= 0.9 * total_demand:
                p90 = d(node) / 60
                break
    features["p90_demand_to_locker_min"] = p90

    # --- step 6: geometry (mean nearest-neighbour distance between lockers) ---
    if n_lockers < 2:
        features["locker_dispersion"] = 0.0
    else:
        nn = []
        for a in locker_nodes:
            best = min(
                _node_distance(city_graph, a, b)
                for b in locker_nodes if b != a
            )
            nn.append(best)
        features["locker_dispersion"] = sum(nn) / len(nn)

    return features


def _node_distance(city_graph, a, b):
    x, y = city_graph.node_coordinates(b)
    return city_graph.distance_to_node(a, x, y)