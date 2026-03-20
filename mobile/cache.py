import os
import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional

DB_PATH = os.path.join(os.path.dirname(__file__), "chat_cache.db")


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_cache() -> None:
    conn = _get_conn()
    with conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY,
                room_id INTEGER NOT NULL,
                sender_id INTEGER NOT NULL,
                content TEXT,
                attachment_url TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
    conn.close()


def save_message(msg: Dict[str, Any]) -> None:
    conn = _get_conn()
    with conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO messages
            (id, room_id, sender_id, content, attachment_url, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                msg.get("id"),
                msg.get("room_id"),
                msg.get("sender_id"),
                msg.get("content"),
                msg.get("attachment_url"),
                msg.get("created_at"),
            ),
        )
    conn.close()


def get_messages(room_id: int, limit: int = 100) -> List[Dict[str, Any]]:
    conn = _get_conn()
    with conn:
        rows = conn.execute(
            "SELECT * FROM messages WHERE room_id = ? ORDER BY created_at DESC LIMIT ?",
            (room_id, limit),
        ).fetchall()
    conn.close()
    return [dict(r) for r in reversed(rows)]
