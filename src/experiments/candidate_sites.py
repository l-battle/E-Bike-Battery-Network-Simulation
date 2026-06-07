"""Candidate locker sites: the menu of possible locations a layout draws from.

Auto-generated from demand hotspots (good spots) plus farthest-point sampling
(spread, for coverage variety), with a CSV override for real sites later.
"""
import csv
import random
import warnings
from pathlib import Path

from src.utils.config import MAX_LOCKER_SNAP_METERS

FIELDNAMES = ["candidate_id", "node_id", "lat", "lon", "source"]


def _demand_seed_nodes(demand):
    """One seed node per hotspot: the node closest to the hotspot centre.

    Zone weights peak at the centre (Gaussian falloff), so the max-weight
    node in a zone is the most central one.
    """
    seeds = []
    for hotspot in demand.hotspots:
        center_node = max(
            zip(hotspot["zone_nodes"], hotspot["zone_weights"]),
            key=lambda pair: pair[1],
        )[0]
        seeds.append(center_node)
    return seeds


def _update_min_dist(city_graph, min_dist, new_node):
    """Update each node's distance-to-nearest-chosen-site with one new site."""
    x, y = city_graph.node_coordinates(new_node)
    for node in min_dist:
        d = city_graph.distance_to_node(node, x, y)
        if d < min_dist[node]:
            min_dist[node] = d


def generate_candidate_sites(city_graph, demand=None, n_sites=40,
                             min_spacing_m=300, seed=0):
    """Demand-seeded farthest-point candidate sites.

    Starts from one node per demand hotspot, then repeatedly adds the node
    farthest from all chosen sites (farthest-point sampling) until n_sites is
    reached or no node is at least min_spacing_m from the nearest chosen site.

    Returns a list of {candidate_id, node_id, lat, lon, source}.
    """
    all_nodes = list(city_graph.graph.nodes)

    # 1. Seeds: demand hotspot centres (or one random node if no demand model).
    if demand is not None and demand.hotspots:
        seeds = list(dict.fromkeys(_demand_seed_nodes(demand)))
    else:
        seeds = [random.Random(seed).choice(all_nodes)]
    seeds = seeds[:n_sites]

    source = {node: "demand" for node in seeds}
    chosen = list(seeds)

    # 2. Farthest-point fill, tracking each node's distance to nearest chosen.
    min_dist = {node: float("inf") for node in all_nodes}
    for s in chosen:
        _update_min_dist(city_graph, min_dist, s)
        min_dist[s] = float("-inf")  # never reselect a chosen site

    while len(chosen) < n_sites:
        node = max(all_nodes, key=lambda n: min_dist[n])
        if min_dist[node] < min_spacing_m:
            break  # nothing left far enough; stop rather than over-pack
        chosen.append(node)
        source[node] = "spread"
        _update_min_dist(city_graph, min_dist, node)
        min_dist[node] = float("-inf")

    # 3. Assemble output rows.
    sites = []
    for i, node in enumerate(chosen):
        x, y = city_graph.node_coordinates(node)
        sites.append({
            "candidate_id": i,
            "node_id": node,
            "lat": y,
            "lon": x,
            "source": source[node],
        })
    return sites


def load_candidate_sites(csv_path, city_graph, max_snap_m=MAX_LOCKER_SNAP_METERS):
    """Load candidate sites from a CSV (lat/lon), snapping each to a node.

    The real-sites override path. lat/lon are authoritative; node_id is
    (re)computed by snapping. Warns if a site snaps further than max_snap_m,
    which usually means the graph has no coverage there.
    """
    sites = []
    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            lat, lon = float(row["lat"]), float(row["lon"])
            node = city_graph.nearest_node(x=lon, y=lat)

            snap = city_graph.distance_to_node(node, x=lon, y=lat)
            if snap > max_snap_m:
                warnings.warn(
                    f"Candidate site {row.get('candidate_id', i)} snapped "
                    f"{snap:.0f} m from its coordinates (> {max_snap_m} m).",
                    stacklevel=2,
                )

            sites.append({
                "candidate_id": int(row.get("candidate_id", i)),
                "node_id": node,
                "lat": lat,
                "lon": lon,
                "source": row.get("source", "csv"),
            })
    return sites


def save_candidate_sites(sites, path):
    """Write candidate sites to a CSV (re-loadable via load_candidate_sites)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(sites)
    return path
