import csv


DATA_FILE = "data/loom_telemetry.csv"


def get_machine_status(loom_id: str) -> dict:
    """Return the latest telemetry reading for a specific loom."""

    records = []

    with open(DATA_FILE, "r", newline="") as file:
        reader = csv.DictReader(file)

        for row in reader:
            if row["loom_id"] == loom_id:
                records.append(row)

    if not records:
        return {
            "success": False,
            "message": f"No data found for loom {loom_id}",
        }

    latest = records[-1]

    return {
        "success": True,
        "loom_id": latest["loom_id"],
        "loom_type": latest["loom_type"],
        "timestamp": latest["timestamp"],
        "rpm": float(latest["rpm"]),
        "temperature": float(latest["temperature"]),
        "vibration": float(latest["vibration"]),
        "motor_current": float(latest["motor_current"]),
        "warp_tension": float(latest["warp_tension"]),
        "weft_tension": float(latest["weft_tension"]),
        "humidity": float(latest["humidity"]),
        "production_rate": float(latest["production_rate"]),
        "efficiency": float(latest["efficiency"]),
        "defect_rate": float(latest["defect_rate"]),
        "machine_status": latest["machine_status"],
        "fault_type": latest["fault_type"],
    }
