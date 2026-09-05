import csv


DATA_FILE = "data/maintenance_history.csv"


def get_maintenance_history(loom_id: str) -> dict:
    """Return maintenance records for a specific loom."""

    records = []

    with open(DATA_FILE, "r", newline="") as file:
        reader = csv.DictReader(file)

        for row in reader:
            if row["loom_id"] == loom_id:
                records.append(row)

    if not records:
        return {
            "success": False,
            "message": f"No maintenance history found for {loom_id}",
        }

    return {
        "success": True,
        "loom_id": loom_id,
        "record_count": len(records),
        "records": records,
    }