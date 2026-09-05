import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.api.main import app


MACHINE = {
    "success": True,
    "loom_id": "L001",
    "loom_type": "Air-Jet",
    "timestamp": "2026-09-05 16:20:30",
    "rpm": 583,
    "temperature": 57.3,
    "vibration": 1.65,
    "motor_current": 10.04,
    "warp_tension": 30.5,
    "weft_tension": 23.8,
    "humidity": 63.3,
    "production_rate": 64.6,
    "efficiency": 63.1,
    "defect_rate": 3.45,
    "machine_status": "WARNING",
    "fault_type": "LOW_PRODUCTION",
}


class ApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_machine_endpoint_returns_telemetry(self):
        with patch("app.api.routes.machine.get_machine_status", return_value=MACHINE):
            response = self.client.get("/api/machines/L001")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["loom_id"], "L001")

    def test_maintenance_endpoint_returns_history(self):
        history = {
            "success": True,
            "loom_id": "L001",
            "record_count": 1,
            "records": [
                {
                    "date": "2026-09-02",
                    "loom_id": "L001",
                    "loom_type": "Air-Jet",
                    "issue": "Low production",
                    "action_taken": "Inspected weft insertion",
                    "technician": "Technician-02",
                    "downtime_hours": "2.0",
                }
            ],
        }
        with patch("app.api.routes.maintenance.get_maintenance_history", return_value=history):
            response = self.client.get("/api/machines/L001/maintenance")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["record_count"], 1)

    def test_diagnosis_endpoint_returns_findings(self):
        diagnosis = {
            "success": True,
            "loom_id": "L001",
            "machine_status": "WARNING",
            "fault_type": "LOW_PRODUCTION",
            "issues": ["Low RPM"],
            "diagnosis": "Potential machine/process anomaly detected.",
        }
        with patch("app.api.routes.diagnosis.diagnose_machine", return_value=diagnosis):
            response = self.client.get("/api/machines/L001/diagnosis")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["issues"], ["Low RPM"])

    def test_research_endpoint_returns_results(self):
        result = {
            "success": True,
            "query": "air jet loom low production",
            "result_count": 1,
            "results": [{"title": "Reference", "url": "https://example.test", "content": "text", "score": 0.9}],
        }
        with patch("app.api.routes.research.web_research", return_value=result):
            response = self.client.post("/api/research", json={"query": result["query"]})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["result_count"], 1)

    def test_agent_endpoint_delegates_to_existing_agent(self):
        with patch("app.api.routes.agent.run_agent", return_value="Machine is operating normally."):
            response = self.client.post("/api/agent", json={"question": "Check L001"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["response"], "Machine is operating normally.")

    def test_root_cause_endpoint_returns_structured_analysis(self):
        analysis = {
            "success": True,
            "loom_id": "L001",
            "analysis_type": "evidence-based root-cause analysis",
            "root_causes": [],
            "summary": "No supported root cause was identified from the available evidence.",
        }
        with patch("app.api.routes.root_cause.root_cause_analysis", return_value=analysis):
            response = self.client.get("/api/machines/L001/root-cause")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["root_causes"], [])

    def test_invalid_loom_returns_400(self):
        failure = {
            "success": False,
            "error_code": "invalid_loom_id",
            "message": "Invalid loom ID",
        }
        with patch("app.api.routes.machine.get_machine_status", return_value=failure):
            response = self.client.get("/api/machines/not-a-loom")
        self.assertEqual(response.status_code, 400)

    def test_unknown_loom_returns_404(self):
        failure = {
            "success": False,
            "error_code": "loom_not_found",
            "message": "No data found for loom L999",
        }
        with patch("app.api.routes.machine.get_machine_status", return_value=failure):
            response = self.client.get("/api/machines/L999")
        self.assertEqual(response.status_code, 404)

    def test_external_research_failure_returns_503(self):
        failure = {
            "success": False,
            "error_code": "research_api_error",
            "error": "Research request failed.",
            "query": "loom fault",
            "result_count": 0,
            "results": [],
        }
        with patch("app.api.routes.research.web_research", return_value=failure):
            response = self.client.post("/api/research", json={"query": "loom fault"})
        self.assertEqual(response.status_code, 503)

    def test_invalid_request_returns_400(self):
        response = self.client.post("/api/research", json={"query": ""})
        self.assertEqual(response.status_code, 400)

    def test_unexpected_tool_failure_returns_500(self):
        with patch(
            "app.api.routes.machine.get_machine_status",
            side_effect=RuntimeError("unexpected storage failure"),
        ):
            response = self.client.get("/api/machines/L001")
        self.assertEqual(response.status_code, 500)

    def test_local_cors_origin_is_allowed(self):
        response = self.client.options(
            "/api/machines/L001",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["access-control-allow-origin"], "http://localhost:3000")


if __name__ == "__main__":
    unittest.main()