from tools.machine_tools import get_machine_status


def diagnose_machine(loom_id: str) -> dict:
    """Analyze a loom's telemetry and identify possible problems."""

    machine = get_machine_status(loom_id)

    if not machine["success"]:
        return machine

    issues = []

    if machine["vibration"] > 3:
        issues.append("High vibration")

    if machine["temperature"] > 65:
        issues.append("High temperature")

    if machine["rpm"] < 600:
        issues.append("Low RPM")

    if machine["motor_current"] > 15:
        issues.append("High motor current")

    if not 25 <= machine["warp_tension"] <= 35:
        issues.append("Abnormal warp tension")

    if not 20 <= machine["weft_tension"] <= 30:
        issues.append("Abnormal weft tension")

    if machine["efficiency"] < 85:
        issues.append("Low efficiency")

    if machine["defect_rate"] > 2:
        issues.append("High defect rate")

    if not issues:
        diagnosis = "Machine operating within normal parameters."
    else:
        diagnosis = "Potential machine/process anomaly detected."

    return {
        "loom_id": loom_id,
        "machine_status": machine["machine_status"],
        "fault_type": machine["fault_type"],
        "issues": issues,
        "diagnosis": diagnosis,
    }