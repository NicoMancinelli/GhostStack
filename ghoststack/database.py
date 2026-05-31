"""SQLite persistence for events and system health."""

import json
import sqlite3
from typing import Any, Dict, List, Optional

from ghoststack.paths import DB_PATH

SCHEMA_EVENTS = """
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    module TEXT,
    event TEXT,
    raw_json TEXT
)
"""

SCHEMA_HEALTH = """
CREATE TABLE IF NOT EXISTS system_health (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    component TEXT,
    status TEXT
)
"""


class EventStore:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.init_schema()

    def _connect(self):
        return sqlite3.connect(self.db_path, check_same_thread=False)

    def init_schema(self):
        conn = self._connect()
        try:
            conn.execute(SCHEMA_EVENTS)
            conn.execute(SCHEMA_HEALTH)
            conn.commit()
        finally:
            conn.close()

    def log_event(self, module: str, event: str, raw_data: Optional[Dict[str, Any]] = None):
        conn = self._connect()
        try:
            conn.execute(
                "INSERT INTO events (module, event, raw_json) VALUES (?, ?, ?)",
                (module, event, json.dumps(raw_data) if raw_data else None),
            )
            conn.commit()
        finally:
            conn.close()

    def log_health(self, component: str, status: str):
        conn = self._connect()
        try:
            conn.execute(
                "INSERT INTO system_health (component, status) VALUES (?, ?)",
                (component, status),
            )
            conn.commit()
        finally:
            conn.close()

    def get_recent_events(self, limit: int = 50) -> List[tuple]:
        conn = self._connect()
        try:
            cur = conn.execute(
                "SELECT * FROM events ORDER BY id DESC LIMIT ?", (limit,)
            )
            return cur.fetchall()
        finally:
            conn.close()

    def get_events_after(self, last_id: int) -> List[tuple]:
        conn = self._connect()
        try:
            cur = conn.execute(
                "SELECT * FROM events WHERE id > ? ORDER BY id ASC", (last_id,)
            )
            return cur.fetchall()
        finally:
            conn.close()

    def get_latest_health(self) -> Dict[str, str]:
        """Latest status row per component."""
        conn = self._connect()
        try:
            cur = conn.execute(
                """
                SELECT component, status FROM system_health sh
                WHERE id = (
                    SELECT MAX(id) FROM system_health
                    WHERE component = sh.component
                )
                """
            )
            return {row[0]: row[1] for row in cur.fetchall()}
        finally:
            conn.close()
