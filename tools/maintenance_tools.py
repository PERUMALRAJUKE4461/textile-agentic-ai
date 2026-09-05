import csv
import logging

from app.config import load_settings


LOGGER = logging.getLogger(__name__)
DATA_FILE = load_settings().maintenance_file


def get_maintenance_history(loom_id: str) -> dict[str, object]:
    """Return maintenance records for a specific loom."""

    records = []

    try:
        with open(DATA_FILE, "r", newline="") as file:
            reader = csv.DictReader(file)

            for row in reader:
                if row.get("loom_id") == loom_id:
                    records.append(row)
    except FileNotFoundError:
        LOGGER.error("Maintenance file is missing: %s", DATA_FILE)
        return {
            "success": False,
            "error_code": "missing_maintenance_data",
            "message": "Maintenance history is unavailable because the data file is missing.",
        }
    except (OSError, csv.Error) as error:
        LOGGER.error("Unable to read maintenance data: %s", error)
        return {
            "success": False,
            "error_code": "maintenance_read_error",
            "message": "Maintenance history could not be read.",
        }

    if not records:
        return {
            "success": False,
            "error_code": "maintenance_not_found",
            "message": f"No maintenance history found for {loom_id}",
        }

    LOGGER.info("Maintenance history loaded for %s", loom_id)
    return {
        "success": True,
        "loom_id": loom_id,
        "record_count": len(records),
        "records": records,
    }