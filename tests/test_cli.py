import unittest
from unittest.mock import call, patch

from app.agent.cli import chat


class ChatCliTests(unittest.TestCase):
    @patch("app.agent.cli.run_agent", side_effect=["L001 is warning.", "Check its air supply."])
    @patch("builtins.print")
    @patch("builtins.input", side_effect=["Investigate loom L001", "What should I check?", "/exit"])
    def test_keeps_conversation_history_between_questions(
        self, mock_input, mock_print, mock_run_agent
    ):
        chat()

        self.assertEqual(
            mock_run_agent.call_args_list,
            [
                call("Investigate loom L001", []),
                call(
                    "What should I check?",
                    [
                        {"role": "user", "content": "Investigate loom L001"},
                        {"role": "assistant", "content": "L001 is warning."},
                    ],
                ),
            ],
        )
        self.assertIn(
            call("\nAssistant: Check its air supply.\n"),
            mock_print.call_args_list,
        )

    @patch("builtins.print")
    @patch("builtins.input", side_effect=["", "/quit"])
    @patch("app.agent.cli.run_agent")
    def test_empty_input_is_ignored_and_quit_exits(
        self, mock_run_agent, mock_input, mock_print
    ):
        chat()

        mock_run_agent.assert_not_called()
        mock_print.assert_any_call("Goodbye.")


if __name__ == "__main__":
    unittest.main()
