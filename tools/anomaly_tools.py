"""Simple, interpretable telemetry anomaly detection."""

from statistics import median, pstdev
from typing import Any

from app.config import Settings, load_settings


ANALYZED_PARAMETERS = (
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


def _threshold_breach(parameter: str, value: float, settings: Settings) -> bool:
    limits = {
        "rpm": value < settings.rpm_minimum,
        "temperature": value > settings.temperature_maximum,
        "vibration": value > settings.vibration_maximum,
        "motor_current": value > settings.motor_current_maximum,
        "warp_tension": not settings.warp_tension_minimum <= value <= settings.warp_tension_maximum,
        "weft_tension": not settings.weft_tension_minimum <= value <= settings.weft_tension_maximum,
        "humidity": value < 45 or value > 75,
        "production_rate": value < 85,
        "efficiency": value < settings.efficiency_minimum,
        "defect_rate": value > settings.defect_rate_maximum,
    }
    return limits[parameter]


def _severity(score: float) -> str:
    if score >= 75:
        return "HIGH"
    if score >= 50:
        return "MEDIUM"
    return "LOW"


def detect_anomalies(
    current: dict[str, Any],
    history: list[dict[str, Any]],
    settings: Settings | None = None,
) -> dict[str, Any]:
    """Compare current values with prior medians and configured limits.

    This is intentionally transparent: each score is based on the distance
    from the prior median relative to a robust tolerance, with a floor when a
    configured prototype threshold is breached. It is not a trained model.
    """
    settings = settings or load_settings()
    prior_records = history[:-1] if history and history[-1].get("timestamp") == current.get("timestamp") else history
    anomalies: list[dict[str, Any]] = []
    baseline_source = "historical median of prior telemetry"

    for parameter in ANALYZED_PARAMETERS:
        value = float(current[parameter])
        values = [float(record[parameter]) for record in prior_records if parameter in record]
        expected = float(median(values)) if values else value
        spread = float(pstdev(values)) if len(values) > 1 else 0.0
        tolerance = max(spread * 2, abs(expected) * 0.05, 0.01)
        deviation = value - expected
        score = min(100.0, abs(deviation) / tolerance * 50)
        if _threshold_breach(parameter, value, settings):
            score = max(score, 65.0)
        score = round(score, 1)
        if score < 50:
            continue
        anomalies.append(
            {
                "parameter": parameter,
                "current_value": round(value, 3),
                "expected_baseline": round(expected, 3),
                "deviation": round(deviation, 3),
                "anomaly_score": score,
                "severity": _severity(score),
                "evidence": (
                    f"Current {parameter} is {round(value, 3)} versus a prior "
                    f"historical median of {round(expected, 3)}."
                ),
            }
        )

    anomalies.sort(key=lambda item: item["anomaly_score"], reverse=True)
    high_count = sum(item["severity"] == "HIGH" for item in anomalies)
    combined_signals = []
    if len(anomalies) >= 3:
        combined_signals.append(
            {
                "parameter": "multi_parameter_operating_pattern",
                "current_value": ", ".join(item["parameter"] for item in anomalies[:5]),
                "expected_baseline": "No simultaneous multi-parameter deviation",
                "deviation": len(anomalies),
                "anomaly_score": round(min(100.0, 50 + high_count * 15 + len(anomalies) * 5), 1),
                "severity": "HIGH" if high_count >= 2 else "MEDIUM",
                "evidence": (
                    f"{len(anomalies)} parameters deviate from historical or configured "
                    "baselines at the same reading."
                ),
            }
        )
    return {
        "method": "historical median deviation plus configured prototype limits",
        "baseline_source": baseline_source,
        "history_count": len(history),
        "anomalies": anomalies,
        "combined_signals": combined_signals,
        "anomaly_count": len(anomalies),
        "overall_severity": "HIGH" if high_count >= 2 else "MEDIUM" if anomalies else "LOW",
        "limitations": [
            "Scores are interpretable evidence scores, not probabilities.",
            "A small history can make the baseline unstable.",
        ],
    }