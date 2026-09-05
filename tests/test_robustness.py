import unittest
from types import SimpleNamespace
from unittest.mock import patch

from app.config import load_settings
from app.agent import tool_agent
from tools import diagnostic_tools, machine_tools, maintenance_tools, research_tools


MACHINE = {
    "success": True,
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


class RobustnessTests(unittest.TestCase):
    def test_configuration_loading_keeps_keys_independent(self):
        settings = load_settings(
            {
                "OPENROUTER_API_KEY": "openrouter-only",
                "TAVILY_API_KEY": "",
                "TEMPERATURE_MAXIMUM": "70",
                "RESEARCH_MAX_RESULTS": "3",
            }
        )
        self.assertEqual(settings.openrouter_api_key, "openrouter-only")
        self.assertIsNone(settings.tavily_api_key)
        self.assertEqual(settings.temperature_maximum, 70)
        self.assertEqual(settings.research_max_results, 3)

    def test_successful_and_invalid_machine_lookup(self):
        self.assertTrue(machine_tools.get_machine_status("L001")["success"])
        result = machine_tools.get_machine_status("invalid")
        self.assertEqual(result["error_code"], "invalid_loom_id")

    def test_missing_telemetry_data_is_graceful(self):
        with patch.object(machine_tools, "DATA_FILE", "missing-telemetry.csv"):
            result = machine_tools.get_machine_status("L001")
        self.assertEqual(result["error_code"], "missing_telemetry_data")

    def test_diagnostic_success_and_failure(self):
        with patch.object(diagnostic_tools, "get_machine_status", return_value=MACHINE):
            result = diagnostic_tools.diagnose_machine("L001")
        self.assertEqual(result["issues"], [])

        failure = {"success": False, "error_code": "loom_not_found", "message": "No data"}
        with patch.object(diagnostic_tools, "get_machine_status", return_value=failure):
            result = diagnostic_tools.diagnose_machine("UNKNOWN")
        self.assertEqual(result, failure)

    def test_maintenance_lookup_and_missing_data(self):
        self.assertTrue(maintenance_tools.get_maintenance_history("L001")["success"])
        with patch.object(maintenance_tools, "DATA_FILE", "missing-maintenance.csv"):
            result = maintenance_tools.get_maintenance_history("L001")
        self.assertEqual(result["error_code"], "missing_maintenance_data")

    def test_research_success_failure_and_empty_results(self):
        settings = SimpleNamespace(tavily_api_key="tavily-key", research_max_results=5)
        with patch.object(research_tools, "load_settings", return_value=settings):
            with patch.object(
                research_tools.tavily_client,
                "search",
                return_value={"results": [{"title": "Reference", "url": "https://example.test"}]},
            ):
                result = research_tools.web_research("loom fault")
        self.assertTrue(result["success"])

        with patch.object(research_tools, "load_settings", return_value=settings):
            with patch.object(research_tools.tavily_client, "search", side_effect=TimeoutError()):
                result = research_tools.web_research("loom fault")
        self.assertEqual(result["error_code"], "research_timeout")

        with patch.object(research_tools, "load_settings", return_value=settings):
            with patch.object(research_tools.tavily_client, "search", return_value={"results": []}):
                result = research_tools.web_research("loom fault")
        self.assertEqual(result["error_code"], "empty_research_results")

        with patch.object(
            research_tools,
            "load_settings",
            return_value=SimpleNamespace(tavily_api_key=None, research_max_results=5),
        ):
            result = research_tools.web_research("loom fault")
        self.assertEqual(result["error_code"], "missing_tavily_api_key")

    def test_tool_execution_failure_is_returned(self):
        with patch.object(tool_agent, "get_machine_status", side_effect=RuntimeError("storage error")):
            result = tool_agent.execute_tool("get_machine_status", {"loom_id": "L001"})
        self.assertEqual(result["error_code"], "tool_execution_error")

    def test_agent_returns_response_after_tool_failure(self):
        tool_call = SimpleNamespace(
            id="call-1",
            function=SimpleNamespace(name="get_machine_status", arguments='{"loom_id":"L001"}'),
        )
        first = SimpleNamespace(tool_calls=[tool_call], content=None)
        second = SimpleNamespace(tool_calls=None, content="The machine lookup failed safely.")
        responses = [
            SimpleNamespace(choices=[SimpleNamespace(message=first)]),
            SimpleNamespace(choices=[SimpleNamespace(message=second)]),
        ]
        fake_client = SimpleNamespace(
            chat=SimpleNamespace(
                completions=SimpleNamespace(create=lambda **kwargs: responses.pop(0))
            )
        )
        settings = SimpleNamespace(
            openrouter_api_key="key", openrouter_model="model", max_agent_rounds=2
        )
        with patch.object(tool_agent, "client", fake_client):
            with patch.object(tool_agent, "load_settings", return_value=settings):
                with patch.object(
                    tool_agent,
                    "execute_tool",
                    return_value={"success": False, "error_code": "loom_not_found"},
                ):
                    result = tool_agent.run_agent("Check L001")
        self.assertEqual(result, "The machine lookup failed safely.")

    def test_agent_handles_missing_key_and_api_failure(self):
        missing_key_settings = SimpleNamespace(
            openrouter_api_key=None, openrouter_model="model", max_agent_rounds=2
        )
        with patch.object(tool_agent, "load_settings", return_value=missing_key_settings):
            result = tool_agent.run_agent("Check L001")
        self.assertIn("OPENROUTER_API_KEY", result)

        failing_settings = SimpleNamespace(
            openrouter_api_key="key", openrouter_model="invalid/model", max_agent_rounds=2
        )
        failing_client = SimpleNamespace(
            chat=SimpleNamespace(
                completions=SimpleNamespace(create=lambda **kwargs: (_ for _ in ()).throw(RuntimeError("bad model")))
            )
        )
        with patch.object(tool_agent, "client", failing_client):
            with patch.object(tool_agent, "load_settings", return_value=failing_settings):
                result = tool_agent.run_agent("Check L001")
        self.assertIn("OpenRouter request failed", result)

    def test_malformed_json_tool_arguments_are_returned_to_agent(self):
        tool_call = SimpleNamespace(
            id="call-2",
            function=SimpleNamespace(name="get_machine_status", arguments="{bad-json"),
        )
        first = SimpleNamespace(tool_calls=[tool_call], content=None)
        second = SimpleNamespace(tool_calls=None, content="Malformed arguments were handled.")
        responses = [
            SimpleNamespace(choices=[SimpleNamespace(message=first)]),
            SimpleNamespace(choices=[SimpleNamespace(message=second)]),
        ]
        fake_client = SimpleNamespace(
            chat=SimpleNamespace(
                completions=SimpleNamespace(create=lambda **kwargs: responses.pop(0))
            )
        )
        settings = SimpleNamespace(
            openrouter_api_key="key", openrouter_model="model", max_agent_rounds=2
        )
        with patch.object(tool_agent, "client", fake_client):
            with patch.object(tool_agent, "load_settings", return_value=settings):
                result = tool_agent.run_agent("Check L001")
        self.assertEqual(result, "Malformed arguments were handled.")


if __name__ == "__main__":
    unittest.main()