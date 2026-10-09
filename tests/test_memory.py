import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.agent import memory


class ConversationMemoryTests(unittest.TestCase):
    def test_turns_persist_and_are_returned_in_order(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "memory.sqlite3"
            with patch.object(memory, "_database_path", return_value=database):
                session_id = "2a79ce38-08b3-4fd1-a4de-b2f0044508a7"
                memory.save_conversation_turn(
                    session_id, "Investigate L001", "L001 is warning."
                )
                memory.save_conversation_turn(
                    session_id, "What should I check?", "Inspect its air supply."
                )

                self.assertEqual(
                    memory.get_conversation_history(session_id, limit=4),
                    [
                        {"role": "user", "content": "Investigate L001"},
                        {"role": "assistant", "content": "L001 is warning."},
                        {"role": "user", "content": "What should I check?"},
                        {"role": "assistant", "content": "Inspect its air supply."},
                    ],
                )

    def test_history_is_isolated_by_session(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "memory.sqlite3"
            with patch.object(memory, "_database_path", return_value=database):
                memory.save_conversation_turn(
                    "2a79ce38-08b3-4fd1-a4de-b2f0044508a7", "Question", "Answer"
                )
                self.assertEqual(
                    memory.get_conversation_history(
                        "770e8400-e29b-41d4-a716-446655440000"
                    ),
                    [],
                )

    def test_invalid_session_id_is_rejected(self):
        with self.assertRaises(ValueError):
            memory.get_conversation_history("not-a-uuid")


if __name__ == "__main__":
    unittest.main()
