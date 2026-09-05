"""Historical telemetry loading for interpretable Phase 6 analysis."""

import csv
import logging
import re
from typing import Any

from app.config import load_settings


LOGGER = logging.getLogger(__name__)
DATA_FILE = load_settings().telemetry_file

NUMERIC_FIELDS = (
    "rpm",
    "temperature",
    "vibration",
    "motor_current",
    "warp_tension",
    "weft_tension",
    "humidity",
    "production_rate",
    "efficiency",
    "defect_rate",
)


def get_telemetry_history(loom_id: str) -> dict[str, Any]:
    """Return all parsed telemetry records for one loom in time order."""
    if not isinstance(loom_id, str) or not re.fullmatch(r"L\d+", loom_id.strip(), re.IGNORECASE):
        return {
            "success": False,
            "error_code": "invalid_loom_id",
            "message": f"Invalid loom ID {loom_id!r}; expected a value such as L001.",
        }

    records: list[dict[str, Any]] = []
    try:
        with open(DATA_FILE, "r", newline="") as file:
            reader = csv.DictReader(file)
            for row in reader:
                if row.get("loom_id") != loom_id.strip().upper():
                    continue
                parsed = dict(row)
                for field in NUMERIC_FIELDS:
                    parsed[field] = float(row[field])
                records.append(parsed)
    except FileNotFoundError:
        LOGGER.error("Telemetry file is missing: %s", DATA_FILE)
        return {
            "success": False,
            "error_code": "missing_telemetry_data",
            "message": "Telemetry data is unavailable because the data file is missing.",
        }
    except (OSError, csv.Error, KeyError, TypeError, ValueError):
        LOGGER.error("Historical telemetry for %s is malformed", loom_id)
        return {
            "success": False,
            "error_code": "malformed_telemetry_data",
            "message": f"Historical telemetry for loom {loom_id} is incomplete or invalid.",
        }

    if not records:
        return {
            "success": False,
            "error_code": "loom_not_found",
            "message": f"No telemetry history found for loom {loom_id}",
        }

    LOGGER.info("Loaded %d historical telemetry records for %s", len(records), loom_id)
    return {
        "success": True,
        "loom_id": loom_id.strip().upper(),
        "record_count": len(records),
        "records": records,
    }