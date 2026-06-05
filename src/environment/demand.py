import csv
import math
import random
import warnings


def load_hotspot_records(csv_path):
    """Read demand hotspots from a CSV file.

    Expected columns: hotspot_id, name, lat, lon, weight, radius_m.
    Returns a list of dicts with typed values.
    """
    records = []

    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)

        for row in reader:
            records.append({
                "hotspot_id": int(row["hotspot_id"]),
                "name": row.get("name", ""),
                "lat": float(row["lat"]),
                "lon": float(row["lon"]),
                "weight": float(row["weight"]),
                "radius_m": float(row["radius_m"]),
            })

    return records


class DemandModel:
    """Weighted spatial demand built from hotspot zones.

    Each hotspot covers a circular zone of graph nodes. Demand is sampled by
    first choosing a hotspot (proportional to its weight) and then a node
    within that hotspot's zone (denser toward the centre via a Gaussian
    falloff). Because the city graph is a single strongly connected
    component, any sampled node is reachable from any other.
    """

    def __init__(self, city_graph, csv_path):
        self.city_graph = city_graph
        self.hotspots = []
        self._build(load_hotspot_records(csv_path))

    def _build(self, records):
        for record in records:
            zone_nodes, zone_weights = self._compute_zone(record)

            if not zone_nodes:
                warnings.warn(
                    f"Hotspot {record['hotspot_id']} ('{record['name']}') has no "
                    f"graph nodes within {record['radius_m']:.0f} m; the graph "
                    f"likely has no coverage there. Skipping it.",
                    stacklevel=3,
                )
                continue

            self.hotspots.append({
                "id": record["hotspot_id"],
                "name": record["name"],
                "weight": record["weight"],
                "zone_nodes": zone_nodes,
                "zone_weights": zone_weights,
            })

        self._hotspot_weights = [h["weight"] for h in self.hotspots]

    def _compute_zone(self, record):
        """All graph nodes within the hotspot radius, with Gaussian weights."""
        radius = record["radius_m"]
        sigma = radius / 2 or 1.0

        nodes = []
        weights = []

        for node in self.city_graph.graph.nodes:
            dist = self.city_graph.distance_to_node(
                node, x=record["lon"], y=record["lat"]
            )
            if dist <= radius:
                nodes.append(node)
                weights.append(math.exp(-(dist ** 2) / (2 * sigma ** 2)))

        return nodes, weights

    @property
    def is_active(self):
        return len(self.hotspots) > 0

    def sample_node(self, exclude=None, max_attempts=10):
        """Sample a graph node according to demand, optionally != exclude."""
        if not self.hotspots:
            raise ValueError("DemandModel has no usable hotspots to sample from.")

        node = None
        for _ in range(max_attempts):
            hotspot = random.choices(
                self.hotspots, weights=self._hotspot_weights
            )[0]
            node = random.choices(
                hotspot["zone_nodes"], weights=hotspot["zone_weights"]
            )[0]

            if node != exclude:
                return node

        return node
