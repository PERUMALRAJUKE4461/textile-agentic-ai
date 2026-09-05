import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.api.main import app
from tools.advanced_analysis_tools import advanced_machine_analysis
from tools.anomaly_tools import detect_anomalies
from tools.prediction_tools import estimate_failure_risk, estimate_maintenance_risk, forecast_production
from tools.trend_tools import INSUFFICIENT_HISTORY_MESSAGE, analyze_trends


def record(index, **overrides):
    value = {
        "timestamp": f"2026-09-05 15:{index:02d}:00",
        "loom_id": "L001",
        "loom_type": "Air-Jet",
        "rpm": 700.0,
        "temperature": 55.0,
        "vibration": 1.2,
        "motor_current": 12.0,
        "warp_tension": 30.0,
        "weft_tension": 25.0,
        "humidity": 60.0,
        "production_rate": 95.0,
        "efficiency": 94.0,
        "defect_rate": 1.0,
        "machine_status": "NORMAL",
        "fault_type": "",
    }
    value.update(overrides)
    return value


class AdvancedAnalysisTests(unittest.TestCase):
    def test_normal_machine_has_no_anomalies(self):
        history = [record(index) for index in range(3)]
        result = detect_anomalies(history[-1], history)
        self.assertEqual(result["anomaly_count"], 0)

    def test_anomalous_machine_returns_explainable_fields(self):
        history = [record(index) for index in range(3)]
        current = record(3, temperature=82.0, vibration=7.1, defect_rate=4.5)
        result = detect_anomalies(current, history + [current])
        parameters = {item["parameter"] for item in result["anomalies"]}
        self.assertIn("temperature", parameters)
        self.assertIn("vibration", parameters)
        self.assertIn("defect_rate", parameters)
        self.assertIn("expected_baseline", result["anomalies"][0])
        self.assertIn("anomaly_score", result["anomalies"][0])

    def test_increasing_vibration_is_deteriorating(self):
        history = [record(index, vibration=1.0 + index * 0.8) for index in range(4)]
        trend = next(item for item in analyze_trends(history)["trends"] if item["parameter"] == "vibration")
        self.assertEqual(trend["direction"], "deteriorating")

    def test_increasing_temperature_is_deteriorating(self):
        history = [record(index, temperature=50 + index * 6) for index in range(4)]
        trend = next(item for item in analyze_trends(history)["trends"] if item["parameter"] == "temperature")
        self.assertEqual(trend["direction"], "deteriorating")

    def test_declining_efficiency_is_deteriorating(self):
        history = [record(index, efficiency=96 - index * 5) for index in range(4)]
        trend = next(item for item in analyze_trends(history)["trends"] if item["parameter"] == "efficiency")
        self.assertEqual(trend["direction"], "deteriorating")

    def test_increasing_defect_rate_is_deteriorating(self):
        history = [record(index, defect_rate=0.5 + index * 1.2) for index in range(4)]
        trend = next(item for item in analyze_trends(history)["trends"] if item["parameter"] == "defect_rate")
        self.assertEqual(trend["direction"], "deteriorating")

    def test_recurring_maintenance_increases_risk_with_evidence(self):
        history = [record(index, vibration=1 + index * 1.0) for index in range(4)]
        current = history[-1]
        anomalies = detect_anomalies(current, history)
        trends = analyze_trends(history)
        maintenance = {
            "success": True,
            "records": [
                {"issue": "Abnormal vibration", "action_taken": "Bearing inspected"},
                {"issue": "Abnormal vibration", "action_taken": "Lubrication performed"},
            ],
        }
        result = estimate_maintenance_risk(current, history, maintenance, anomalies, trends)
        self.assertIn(result["risk"], {"MEDIUM", "HIGH"})
        self.assertTrue(result["evidence"])

    def test_insufficient_history_is_explicit(self):
        history = [record(0), record(1)]
        trends = analyze_trends(history)
        forecast = forecast_production(history[-1], history)
        self.assertEqual(trends["message"], INSUFFICIENT_HISTORY_MESSAGE)
        self.assertEqual(forecast["message"], INSUFFICIENT_HISTORY_MESSAGE)

    def test_failure_risk_is_not_certainty(self):
        history = [record(index) for index in range(3)]
        current = record(3, production_rate=65, fault_type="LOW_PRODUCTION")
        anomalies = detect_anomalies(current, history + [current])
        risks = estimate_failure_risk(current, {"success": True, "records": []}, anomalies, analyze_trends(history + [current]))
        low_production = next(item for item in risks["risks"] if item["failure_mode"] == "LOW_PRODUCTION")
        self.assertIn("does not confirm", low_production["message"])

    def test_combined_analysis_calls_existing_root_cause_path(self):
        current = record(3, production_rate=65, efficiency=70, fault_type="LOW_PRODUCTION", machine_status="WARNING")
        current["success"] = True
        history = [record(index) for index in range(3)] + [current]
        maintenance = {"success": True, "records": []}
        diagnosis = {"success": True, "issues": ["Low efficiency"]}
        root_cause = {"success": True, "loom_id": "L001", "analysis_type": "evidence", "root_causes": [], "summary": "test"}
        with patch("tools.advanced_analysis_tools.get_machine_status", return_value=current):
            with patch("tools.advanced_analysis_tools.get_telemetry_history", return_value={"success": True, "records": history}):
                with patch("tools.advanced_analysis_tools.get_maintenance_history", return_value=maintenance):
                    with patch("tools.advanced_analysis_tools.diagnose_machine", return_value=diagnosis):
                        with patch("tools.advanced_analysis_tools.root_cause_analysis", return_value=root_cause):
                            result = advanced_machine_analysis("L001")
        self.assertTrue(result["success"])
        self.assertIn("anomaly_detection", result)
        self.assertIn("production_forecast", result)
        self.assertEqual(result["root_cause_analysis"], root_cause)

    def test_advanced_api_returns_combined_analysis(self):
        payload = {
            "success": True,
            "loom_id": "L001",
            "current_telemetry": record(3),
            "historical_record_count": 4,
            "diagnostic": {},
            "maintenance_history": {},
            "anomaly_detection": {},
            "trend_analysis": {},
            "predictive_maintenance": {},
            "production_forecast": {},
            "failure_risk": {},
            "root_cause_analysis": {},
            "limitations": [INSUFFICIENT_HISTORY_MESSAGE],
            "explainability": "Evidence included.",
        }
        with patch("app.api.routes.advanced.advanced_machine_analysis", return_value=payload):
            response = TestClient(app).get("/api/machines/L001/advanced-analysis")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["historical_record_count"], 4)


if __name__ == "__main__":
    unittest.main()