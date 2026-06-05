import csv


def load_ferry_records(csv_path):
    """Read ferry crossings from a CSV file.

    Expected columns: name, from_lat, from_lon, to_lat, to_lon,
    crossing_seconds, wait_seconds. Returns a list of typed dicts.
    """
    records = []

    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)

        for row in reader:
            records.append({
                "name": row.get("name", "ferry"),
                "from_lat": float(row["from_lat"]),
                "from_lon": float(row["from_lon"]),
                "to_lat": float(row["to_lat"]),
                "to_lon": float(row["to_lon"]),
                "crossing_seconds": float(row["crossing_seconds"]),
                "wait_seconds": float(row["wait_seconds"]),
            })

    return records
