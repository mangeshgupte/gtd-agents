"""SQLite models for GTD items and projects."""

import sqlite3
import uuid
from datetime import datetime, date
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional

DB_PATH = Path.home() / ".gtd" / "gtd.db"


@dataclass
class Item:
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    raw_text: str = ""
    type: str = "inbox"  # inbox|action|project|waiting|someday|reference|trash
    context: Optional[str] = None  # @home|@computer|@errands|@calls|@office|@anywhere
    energy: Optional[str] = None  # low|medium|high
    time_est: Optional[int] = None  # minutes
    deadline: Optional[str] = None  # ISO date
    project_id: Optional[str] = None
    delegated_to: Optional[str] = None
    status: str = "active"  # active|completed|dropped
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    clarified_at: Optional[str] = None
    next_review: Optional[str] = None
    notes: Optional[str] = None


@dataclass
class Project:
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    name: str = ""
    status: str = "active"  # active|completed|on_hold|dropped
    next_action_id: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


def get_db() -> sqlite3.Connection:
    """Get a database connection, creating tables if needed."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    _create_tables(conn)
    return conn


def _create_tables(conn: sqlite3.Connection):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS items (
            id TEXT PRIMARY KEY,
            raw_text TEXT NOT NULL,
            type TEXT NOT NULL DEFAULT 'inbox',
            context TEXT,
            energy TEXT,
            time_est INTEGER,
            deadline TEXT,
            project_id TEXT REFERENCES projects(id),
            delegated_to TEXT,
            status TEXT NOT NULL DEFAULT 'active',
            created_at TEXT NOT NULL,
            clarified_at TEXT,
            next_review TEXT,
            notes TEXT
        );

        CREATE TABLE IF NOT EXISTS projects (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'active',
            next_action_id TEXT REFERENCES items(id),
            created_at TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_items_type ON items(type);
        CREATE INDEX IF NOT EXISTS idx_items_status ON items(status);
        CREATE INDEX IF NOT EXISTS idx_items_context ON items(context);
        CREATE INDEX IF NOT EXISTS idx_items_project ON items(project_id);
    """)


def add_item(conn: sqlite3.Connection, item: Item) -> Item:
    conn.execute(
        """INSERT INTO items (id, raw_text, type, context, energy, time_est,
           deadline, project_id, delegated_to, status, created_at, clarified_at,
           next_review, notes)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (item.id, item.raw_text, item.type, item.context, item.energy,
         item.time_est, item.deadline, item.project_id, item.delegated_to,
         item.status, item.created_at, item.clarified_at, item.next_review,
         item.notes)
    )
    conn.commit()
    return item


def get_items(conn: sqlite3.Connection, type: Optional[str] = None,
              status: str = "active", context: Optional[str] = None) -> list[dict]:
    query = "SELECT * FROM items WHERE status = ?"
    params: list = [status]
    if type:
        query += " AND type = ?"
        params.append(type)
    if context:
        query += " AND context = ?"
        params.append(context)
    query += " ORDER BY created_at DESC"
    return [dict(row) for row in conn.execute(query, params).fetchall()]


def get_item(conn: sqlite3.Connection, item_id: str) -> Optional[dict]:
    row = conn.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()
    return dict(row) if row else None


def update_item(conn: sqlite3.Connection, item_id: str, **kwargs) -> bool:
    if not kwargs:
        return False
    sets = ", ".join(f"{k} = ?" for k in kwargs)
    vals = list(kwargs.values()) + [item_id]
    conn.execute(f"UPDATE items SET {sets} WHERE id = ?", vals)
    conn.commit()
    return conn.total_changes > 0


def add_project(conn: sqlite3.Connection, project: Project) -> Project:
    conn.execute(
        "INSERT INTO projects (id, name, status, next_action_id, created_at) VALUES (?, ?, ?, ?, ?)",
        (project.id, project.name, project.status, project.next_action_id, project.created_at)
    )
    conn.commit()
    return project


def get_projects(conn: sqlite3.Connection, status: str = "active") -> list[dict]:
    return [dict(row) for row in
            conn.execute("SELECT * FROM projects WHERE status = ? ORDER BY created_at DESC",
                         (status,)).fetchall()]


def get_project(conn: sqlite3.Connection, project_id: str) -> Optional[dict]:
    row = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
    return dict(row) if row else None
