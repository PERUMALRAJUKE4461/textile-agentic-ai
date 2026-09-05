import csv
import logging
import re

from app.config import load_settings


LOGGER = logging.getLogger(__name__)
DATA_FILE = load_settings().telemetry_file


def _invalid_loom_id(loom_id: str) -> dict[str, object]:
    return {
        "success": False,
        "error_code": "invalid_loom_id",
        "message": f"Invalid loom ID {loom_id!r}; expected a value such as L001.",
    }


def get_machine_status(loom_id: str) -> dict[str, object]:
    """Return the latest telemetry reading for a specific loom."""

    if not isinstance(loom_id, str) or not re.fullmatch(r"L\d+", loom_id.strip(), re.IGNORECASE):
        return _invalid_loom_id(loom_id)

    records = []

    try:
        with open(DATA_FILE, "r", newline="") as file:
            reader = csv.DictReader(file)

            for row in reader:
                if row.get("loom_id") == loom_id.strip().upper():
                    records.append(row)
    except FileNotFoundError:
        LOGGER.error("Telemetry file is missing: %s", DATA_FILE)
        return {
            "success": False,
            "error_code": "missing_telemetry_data",
            "message": "Telemetry data is unavailable because the data file is missing.",
        }
    except (OSError, csv.Error) as error:
        LOGGER.error("Unable to read telemetry data: %s", error)
        return {
            "success": False,
            "error_code": "telemetry_read_error",
            "message": "Telemetry data could not be read.",
        }

    if not records:
        return {
            "success": False,
            "error_code": "loom_not_found",
            "message": f"No data found for loom {loom_id}",
        }

    latest = records[-1]

    try:
        result = {
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
    except (KeyError, TypeError, ValueError):
        LOGGER.error("Telemetry row for %s is malformed", loom_id)
        return {
            "success": False,
            "error_code": "malformed_telemetry_data",
            "message": f"Telemetry data for loom {loom_id} is incomplete or invalid.",
        }

    LOGGER.info("Machine status loaded for %s", loom_id)
    return result
