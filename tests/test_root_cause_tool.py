import unittest
from unittest.mock import patch

from tools.root_cause_tools import analyze_root_causes, root_cause_analysis


def machine(**overrides):
    result = {
        "success": True,
        "loom_id": "TEST-01",
        "loom_type": "Air-Jet",
        "rpm": 700,
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
    result.update(overrides)
    return result


def diagnosis(*issues):
    return {"success": True, "issues": list(issues)}


class RootCauseAnalysisTests(unittest.TestCase):
    def test_normal_machine_has_no_suspected_causes(self):
        result = analyze_root_causes(
            machine(), {"success": True, "records": []}, diagnosis(), []
        )
        self.assertEqual(result["root_causes"], [])

    def test_low_production_ranks_air_and_uses_maintenance_evidence(self):
        result = analyze_root_causes(
            machine(production_rate=64.6, efficiency=63.1, fault_type="LOW_PRODUCTION"),
            {
                "success": True,
                "records": [
                    {
                        "issue": "Low production",
                        "action_taken": "Air nozzle cleaned and pressure checked",
                    },
                    {
                        "issue": "Low production",
                        "action_taken": "Weft insertion system inspected",
                    },
                ],
            },
            diagnosis("Low efficiency", "Low production"),
            [{"title": "Air jet troubleshooting", "url": "https://example.test", "content": "pressure and nozzle"}],
        )
        self.assertEqual(result["root_causes"][0]["cause"], "Air supply problem")
        self.assertGreaterEqual(result["root_causes"][0]["confidence_score"], 0)
        self.assertEqual(
            len(result["root_causes"][0]["evidence"]["relevant_maintenance_history"]),
            2,
        )
        self.assertEqual(
            result["root_causes"][0]["evidence"]["supporting_web_research"][0]["type"],
            "WEB REFERENCE",
        )

    def test_high_vibration_identifies_mechanical_issue(self):
        result = analyze_root_causes(
            machine(vibration=7.25, temperature=69.4, motor_current=16.66, fault_type="BEARING_FAULT"),
            {"success": True, "records": []},
            diagnosis("High vibration", "High temperature"),
            [],
        )
        self.assertEqual(result["root_causes"][0]["cause"], "Mechanical or bearing issue")

    def test_high_temperature_identifies_thermal_issue(self):
        result = analyze_root_causes(
            machine(temperature=80.9, efficiency=71.2, fault_type="OVERHEATING"),
            {"success": True, "records": []},
            diagnosis("High temperature"),
            [],
        )
        causes = {item["cause"] for item in result["root_causes"]}
        self.assertIn("Cooling or thermal issue", causes)

    def test_high_defect_rate_identifies_tension_issue(self):
        result = analyze_root_causes(
            machine(defect_rate=4.41, warp_tension=38.0, weft_tension=35.5, fault_type="YARN_TENSION_FAULT"),
            {"success": True, "records": []},
            diagnosis("High defect rate", "Abnormal warp tension", "Abnormal weft tension"),
            [],
        )
        causes = {item["cause"] for item in result["root_causes"]}
        self.assertIn("Yarn tension or weft process issue", causes)

    def test_unknown_loom_returns_local_error_without_research(self):
        with patch("tools.root_cause_tools.get_machine_status") as get_status:
            get_status.return_value = {"success": False, "message": "No data"}
            with patch("tools.root_cause_tools.web_research") as research:
                result = root_cause_analysis("UNKNOWN")
        self.assertFalse(result["success"])
        research.assert_not_called()

    def test_failed_web_research_is_reported_without_losing_local_analysis(self):
        with (
            patch("tools.root_cause_tools.get_machine_status", return_value=machine(production_rate=64.6)),
            patch("tools.root_cause_tools.get_maintenance_history", return_value={"success": True, "records": []}),
            patch("tools.root_cause_tools.diagnose_machine", return_value=diagnosis("Low production")),
            patch(
            "tools.root_cause_tools.web_research",
            return_value={"success": False, "results": [], "error": "network unavailable"},
            ),
        ):
            result = root_cause_analysis("TEST-01")

        self.assertFalse(result["research_available"])
        self.assertIn("unavailable", result["research_note"])
        self.assertTrue(result["root_causes"])
        self.assertTrue(all("WEB REFERENCE" not in str(item) for item in result["root_causes"]))


if __name__ == "__main__":
    unittest.main()