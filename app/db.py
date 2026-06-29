import json
import os
import sqlite3
from datetime import datetime, timezone
from typing import Optional


def _db_path() -> str:
    url = os.getenv("DATABASE_URL", "sqlite:///triagebot.db")
    return url.removeprefix("sqlite:///")


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(_db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tickets (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            title       TEXT NOT NULL,
            description TEXT NOT NULL,
            category    TEXT NOT NULL,
            priority    TEXT NOT NULL,
            tags        TEXT NOT NULL DEFAULT '[]',
            status      TEXT NOT NULL DEFAULT 'open',
            created_at  TEXT NOT NULL,
            updated_at  TEXT NOT NULL
        )
    """)
    return conn


def init_db() -> None:
    get_conn().close()


def create_ticket(title: str, description: str, category: str, priority: str, tags: list[str]) -> dict:
    now = datetime.now(timezone.utc).isoformat()
    with get_conn() as conn:
        cur = conn.execute(
            """
            INSERT INTO tickets (title, description, category, priority, tags, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, 'open', ?, ?)
            """,
            (title, description, category, priority, json.dumps(tags), now, now),
        )
        new_id = cur.lastrowid
    return get_ticket(new_id)


def get_ticket(ticket_id: int) -> Optional[dict]:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
    return _row_to_dict(row) if row else None


def list_tickets(category: Optional[str] = None, priority: Optional[str] = None, status: Optional[str] = None) -> list[dict]:
    query = "SELECT * FROM tickets WHERE 1=1"
    params: list = []
    if category:
        query += " AND category = ?"
        params.append(category)
    if priority:
        query += " AND priority = ?"
        params.append(priority)
    if status:
        query += " AND status = ?"
        params.append(status)
    query += " ORDER BY id"
    with get_conn() as conn:
        rows = conn.execute(query, params).fetchall()
    return [_row_to_dict(r) for r in rows]


def update_ticket(ticket_id: int, status: Optional[str], priority: Optional[str]) -> Optional[dict]:
    fields, params = [], []
    if status is not None:
        fields.append("status = ?")
        params.append(status)
    if priority is not None:
        fields.append("priority = ?")
        params.append(priority)
    if not fields:
        return get_ticket(ticket_id)
    now = datetime.now(timezone.utc).isoformat()
    fields.append("updated_at = ?")
    params.extend([now, ticket_id])
    with get_conn() as conn:
        conn.execute(f"UPDATE tickets SET {', '.join(fields)} WHERE id = ?", params)
    return get_ticket(ticket_id)


def _row_to_dict(row: sqlite3.Row) -> dict:
    d = dict(row)
    d["tags"] = json.loads(d["tags"])
    return d
