"""Phase 6 orchestration for explainable advanced machine analysis."""

import logging
from typing import Any

from tools.anomaly_tools import detect_anomalies
from tools.diagnostic_tools import diagnose_machine
from tools.historical_tools import get_telemetry_history
from tools.machine_tools import get_machine_status
from tools.maintenance_tools import get_maintenance_history
from tools.prediction_tools import (
    estimate_failure_risk,
    estimate_maintenance_risk,
    forecast_production,
)
from tools.root_cause_tools import root_cause_analysis
from tools.trend_tools import analyze_trends


LOGGER = logging.getLogger(__name__)
INSUFFICIENT_HISTORY_MESSAGE = "Insufficient historical data for reliable prediction."


def advanced_machine_analysis(loom_id: str) -> dict[str, Any]:
    """Combine telemetry, historical analysis, diagnosis, RCA, and predictions.

    The returned prediction fields are explicitly estimates. No synthetic
    telemetry or fabricated maintenance records are created when data is
    missing.
    """
    current = get_machine_status(loom_id)
    if not current.get("success", False):
        return current

    history_result = get_telemetry_history(loom_id)
    if not history_result.get("success", False):
        return history_result
    history = history_result["records"]
    maintenance = get_maintenance_history(loom_id)
    diagnosis = diagnose_machine(loom_id)
    anomaly_detection = detect_anomalies(current, history)
    trends = analyze_trends(history)
    maintenance_risk = estimate_maintenance_risk(
        current, history, maintenance, anomaly_detection, trends
    )
    production_forecast = forecast_production(current, history)
    failure_risk = estimate_failure_risk(current, maintenance, anomaly_detection, trends)
    root_cause = root_cause_analysis(loom_id)

    limitations = [
        "These are interpretable estimates based on the available telemetry history, not certain predictions.",
        "Prototype thresholds and small CSV history should be replaced with OEM limits and production-grade models when more labeled data is available.",
    ]
    if len(history) < 3:
        limitations.insert(0, INSUFFICIENT_HISTORY_MESSAGE)

    return {
        "success": True,
        "loom_id": loom_id,
        "current_telemetry": current,
        "historical_record_count": len(history),
        "diagnostic": diagnosis,
        "maintenance_history": maintenance,
        "anomaly_detection": anomaly_detection,
        "trend_analysis": trends,
        "predictive_maintenance": maintenance_risk,
        "production_forecast": production_forecast,
        "failure_risk": failure_risk,
        "root_cause_analysis": root_cause,
        "limitations": limitations,
        "explainability": "Every anomaly, trend, risk, and forecast includes the telemetry or maintenance evidence used to derive it.",
    }