import logging

from app.config import load_settings
from tools.machine_tools import get_machine_status


LOGGER = logging.getLogger(__name__)


def diagnose_machine(loom_id: str) -> dict[str, object]:
    """Analyze a loom's telemetry and identify possible problems."""

    machine = get_machine_status(loom_id)

    if not machine.get("success", False):
        return machine

    settings = load_settings()
    issues = []

    if machine["vibration"] > settings.vibration_maximum:
        issues.append("High vibration")

    if machine["temperature"] > settings.temperature_maximum:
        issues.append("High temperature")

    if machine["rpm"] < settings.rpm_minimum:
        issues.append("Low RPM")

    if machine["motor_current"] > settings.motor_current_maximum:
        issues.append("High motor current")

    if not settings.warp_tension_minimum <= machine["warp_tension"] <= settings.warp_tension_maximum:
        issues.append("Abnormal warp tension")

    if not settings.weft_tension_minimum <= machine["weft_tension"] <= settings.weft_tension_maximum:
        issues.append("Abnormal weft tension")

    if machine["efficiency"] < settings.efficiency_minimum:
        issues.append("Low efficiency")

    if machine["defect_rate"] > settings.defect_rate_maximum:
        issues.append("High defect rate")

    if not issues:
        diagnosis = "Machine operating within normal parameters."
    else:
        diagnosis = "Potential machine/process anomaly detected."

    result = {
        "success": True,
        "loom_id": loom_id,
        "machine_status": machine["machine_status"],
        "fault_type": machine["fault_type"],
        "issues": issues,
        "diagnosis": diagnosis,
    }
    LOGGER.info("Machine diagnosis completed for %s", loom_id)
    return result