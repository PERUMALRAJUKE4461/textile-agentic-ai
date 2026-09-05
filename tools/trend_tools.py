"""Interpretable trend classification for telemetry history."""

from typing import Any

from tools.anomaly_tools import ANALYZED_PARAMETERS


INSUFFICIENT_HISTORY_MESSAGE = "Insufficient historical data for reliable prediction."
HIGHER_IS_BETTER = {"rpm", "production_rate", "efficiency"}


def _classification(parameter: str, change_percent: float) -> str:
    if abs(change_percent) < 3:
        return "stable"
    improving = change_percent > 0 if parameter in HIGHER_IS_BETTER else change_percent < 0
    return "improving" if improving else "deteriorating"


def analyze_trends(history: list[dict[str, Any]]) -> dict[str, Any]:
    """Classify each metric as improving, stable, or deteriorating."""
    if len(history) < 3:
        return {
            "status": "insufficient_data",
            "message": INSUFFICIENT_HISTORY_MESSAGE,
            "trends": [],
            "history_count": len(history),
        }

    trends = []
    for parameter in ANALYZED_PARAMETERS:
        values = [float(record[parameter]) for record in history]
        first_value = values[0]
        last_value = values[-1]
        change_percent = ((last_value - first_value) / max(abs(first_value), 0.01)) * 100
        direction = _classification(parameter, change_percent)
        trends.append(
            {
                "parameter": parameter,
                "direction": direction,
                "first_value": round(first_value, 3),
                "latest_value": round(last_value, 3),
                "change_percent": round(change_percent, 2),
                "confidence": min(90, 40 + len(history) * 8),
                "evidence": (
                    f"{parameter} changed from {round(first_value, 3)} to "
                    f"{round(last_value, 3)} across {len(history)} readings."
                ),
            }
        )
    return {
        "status": "available",
        "history_count": len(history),
        "trends": trends,
        "method": "first-to-latest relative change with a 3% stability band",
    }