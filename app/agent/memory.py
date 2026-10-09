"""SQLite-backed conversation history for the API assistant."""

import sqlite3
from contextlib import closing
from pathlib import Path
from uuid import UUID

from app.config import load_settings


def _database_path() -> Path:
    return Path(load_settings().chat_memory_file)


def _connect() -> sqlite3.Connection:
    path = _database_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, timeout=10)
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS conversations (
            session_id TEXT PRIMARY KEY,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS conversation_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL REFERENCES conversations(session_id),
            role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
            content TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    return connection


def _validate_session_id(session_id: str) -> str:
    try:
        return str(UUID(session_id))
    except (AttributeError, TypeError, ValueError) as error:
        raise ValueError("session_id must be a valid UUID.") from error


def get_conversation_history(
    session_id: str, limit: int = 40
) -> list[dict[str, str]]:
    """Return the most recent conversation messages in chronological order."""
    normalized_id = _validate_session_id(session_id)
    if limit < 1:
        raise ValueError("limit must be positive.")

    with closing(_connect()) as connection, connection:
        rows = connection.execute(
            """
            SELECT role, content
            FROM (
                SELECT id, role, content
                FROM conversation_messages
                WHERE session_id = ?
                ORDER BY id DESC
                LIMIT ?
            )
            ORDER BY id ASC
            """,
            (normalized_id, limit),
        ).fetchall()
    return [{"role": role, "content": content} for role, content in rows]


def save_conversation_turn(
    session_id: str, question: str, response: str
) -> None:
    """Persist one successful user/assistant exchange atomically."""
    normalized_id = _validate_session_id(session_id)
    if not question.strip() or not response.strip():
        raise ValueError("Conversation messages must not be empty.")

    with closing(_connect()) as connection, connection:
        connection.execute(
            """
            INSERT INTO conversations (session_id)
            VALUES (?)
            ON CONFLICT(session_id) DO UPDATE
            SET updated_at = CURRENT_TIMESTAMP
            """,
            (normalized_id,),
        )
        connection.executemany(
            """
            INSERT INTO conversation_messages (session_id, role, content)
            VALUES (?, ?, ?)
            """,
            [
                (normalized_id, "user", question),
                (normalized_id, "assistant", response),
            ],
        )
