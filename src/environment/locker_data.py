import csv


def load_locker_records(csv_path):
    """Read locker definitions from a CSV file.

    Expected columns: locker_id, name, lat, lon, charged_batteries, capacity.
    Returns a list of dicts with typed values. Coordinates stay as lat/lon;
    snapping to graph nodes is the model's responsibility.
    """
    records = []

    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)

        for row in reader:
            records.append({
                "locker_id": int(row["locker_id"]),
                "name": row.get("name", ""),
                "lat": float(row["lat"]),
                "lon": float(row["lon"]),
                "charged_batteries": int(row["charged_batteries"]),
                "capacity": int(row["capacity"]),
            })

    return records
