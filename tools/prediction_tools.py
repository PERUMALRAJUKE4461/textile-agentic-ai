"""Explainable maintenance, production, and failure risk estimates."""

from statistics import pstdev
from typing import Any

from tools.trend_tools import INSUFFICIENT_HISTORY_MESSAGE


def _evidence(detail: str, evidence_type: str = "OBSERVED FACT") -> dict[str, str]:
    return {"type": evidence_type, "detail": detail}


def _trend_map(trends: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {item["parameter"]: item for item in trends.get("trends", [])}


def estimate_maintenance_risk(
    current: dict[str, Any],
    history: list[dict[str, Any]],
    maintenance: dict[str, Any],
    anomalies: dict[str, Any],
    trends: dict[str, Any],
) -> dict[str, Any]:
    """Estimate maintenance risk from current signals, trends, and history."""
    if len(history) < 3:
        return {
            "risk": "UNKNOWN",
            "confidence": 0,
            "message": INSUFFICIENT_HISTORY_MESSAGE,
            "evidence": [_evidence("Fewer than three telemetry readings are available.", "INFERENCE")],
            "limitations": ["No reliable maintenance risk classification is made with this history size."],
        }

    evidence = []
    score = 0
    high_anomalies = [item for item in anomalies.get("anomalies", []) if item["severity"] == "HIGH"]
    if high_anomalies:
        score += min(45, len(high_anomalies) * 15)
        evidence.append(_evidence(f"{len(high_anomalies)} telemetry anomalies have HIGH severity."))

    trend_map = _trend_map(trends)
    deteriorating = [
        parameter for parameter in ("vibration", "temperature", "defect_rate", "efficiency", "production_rate")
        if trend_map.get(parameter, {}).get("direction") == "deteriorating"
    ]
    if deteriorating:
        score += min(30, len(deteriorating) * 10)
        evidence.append(_evidence(f"Deteriorating trends were detected for: {', '.join(deteriorating)}."))

    records = maintenance.get("records", []) if maintenance.get("success", False) else []
    issue_text = " ".join(str(record.get("issue", "")) for record in records).lower()
    recurring = len(records) >= 2 and any(issue in issue_text for issue in ("production", "vibration", "temperature", "bearing", "weft"))
    if recurring:
        score += 20
        evidence.append(_evidence(f"Maintenance history contains {len(records)} relevant prior service records."))

    if current.get("machine_status") in {"WARNING", "CRITICAL"}:
        score += 15
        evidence.append(_evidence(f"Current machine status is {current['machine_status']}."))

    risk = "HIGH" if score >= 60 else "MEDIUM" if score >= 30 else "LOW"
    return {
        "risk": risk,
        "confidence": min(90, 35 + len(evidence) * 12),
        "evidence": evidence or [_evidence("No strong maintenance risk signals were found.")],
        "explanation": "This is an evidence-based maintenance risk estimate, not a failure date prediction.",
        "limitations": ["The available dataset is small and does not support exact failure timing."],
    }


def forecast_production(current: dict[str, Any], history: list[dict[str, Any]]) -> dict[str, Any]:
    """Estimate the next production reading from the observed linear trend."""
    if len(history) < 3:
        return {
            "status": "insufficient_data",
            "message": INSUFFICIENT_HISTORY_MESSAGE,
            "current_production": current.get("production_rate"),
            "forecast": None,
            "confidence": 0,
            "uncertainty": None,
        }

    values = [float(record["production_rate"]) for record in history]
    step_change = (values[-1] - values[0]) / (len(values) - 1)
    forecast = max(0.0, min(100.0, values[-1] + step_change))
    uncertainty = max(2.0, pstdev(values))
    confidence = max(20, min(85, round(80 - uncertainty * 2 + len(values) * 2)))
    trend = "improving" if step_change > 0.5 else "deteriorating" if step_change < -0.5 else "stable"
    return {
        "status": "estimate",
        "current_production": round(float(current["production_rate"]), 2),
        "historical_trend": trend,
        "forecast": round(forecast, 2),
        "confidence": confidence,
        "uncertainty": round(uncertainty, 2),
        "horizon": "next comparable telemetry reading",
        "explanation": "Forecast is a one-step estimate from the historical production slope; it is not a guarantee.",
    }


def estimate_failure_risk(
    current: dict[str, Any],
    maintenance: dict[str, Any],
    anomalies: dict[str, Any],
    trends: dict[str, Any],
) -> dict[str, Any]:
    """Estimate risk for named failure modes using transparent rules."""
    trend_map = _trend_map(trends)
    maintenance_text = " ".join(
        str(value).lower()
        for record in maintenance.get("records", [])
        for value in record.values()
    )
    anomaly_parameters = {item["parameter"] for item in anomalies.get("anomalies", [])}
    definitions = {
        "LOW_PRODUCTION": (
            current.get("production_rate", 100) < 85,
            "production_rate",
            "Current production is below the prototype operating threshold.",
        ),
        "HIGH_VIBRATION": (
            current.get("vibration", 0) > 3,
            "vibration",
            "Current vibration exceeds the prototype operating threshold.",
        ),
        "HIGH_TEMPERATURE": (
            current.get("temperature", 0) > 65,
            "temperature",
            "Current temperature exceeds the prototype operating threshold.",
        ),
        "WEFT_INSERTION_FAILURE": (
            "air" in str(current.get("loom_type", "")).lower()
            and (current.get("production_rate", 100) < 85 or "weft" in maintenance_text),
            "production_rate",
            "Air-jet production evidence and/or prior weft insertion service support this risk signal.",
        ),
    }
    risks = []
    for failure_mode, (direct_signal, parameter, detail) in definitions.items():
        score = 25 if direct_signal else 5
        evidence = [_evidence(detail)] if direct_signal else []
        if parameter in anomaly_parameters:
            score += 25
            evidence.append(_evidence(f"Anomaly detection flagged {parameter} against its historical baseline."))
        if trend_map.get(parameter, {}).get("direction") == "deteriorating":
            score += 25
            evidence.append(_evidence(f"The {parameter} trend is deteriorating."))
        score = min(100, score)
        risks.append(
            {
                "failure_mode": failure_mode,
                "risk": "HIGH" if score >= 70 else "MEDIUM" if score >= 35 else "LOW",
                "score": score,
                "confidence": min(85, 35 + len(evidence) * 15),
                "evidence": evidence or [_evidence("No direct current or historical signal was found.", "INFERENCE")],
                "message": "Risk estimate only; this does not confirm that a failure will occur.",
            }
        )
    return {"risks": sorted(risks, key=lambda item: item["score"], reverse=True)}