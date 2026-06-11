"""
state/action_store.py

Persistent action queue backed by SQLite, with in-memory dict fallback.
"""

import json
import os
import uuid
from datetime import datetime, timezone

DB_PATH = os.path.join(os.path.dirname(__file__), "actions.db")

# --- SQLite setup -----------------------------------------------------------

def _get_conn():
    import sqlite3
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def _init_db():
    try:
        with _get_conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS actions (
                    id          TEXT PRIMARY KEY,
                    action_type TEXT NOT NULL,
                    params      TEXT NOT NULL,
                    proposed_by TEXT NOT NULL,
                    status      TEXT NOT NULL DEFAULT 'pending',
                    created_at  TEXT NOT NULL,
                    updated_at  TEXT NOT NULL,
                    result      TEXT,
                    error       TEXT
                )
            """)
        return True
    except Exception:
        return False

_USE_SQLITE = _init_db()

# --- In-memory fallback -----------------------------------------------------

_store: dict[str, dict] = {}

# --- Internal helpers --------------------------------------------------------

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

def _row_to_dict(row) -> dict:
    d = dict(row)
    d["params"] = json.loads(d["params"])
    d["result"] = json.loads(d["result"]) if d["result"] else None
    return d

# --- Public API -------------------------------------------------------------

def enqueue(action_type: str, params: dict, proposed_by: str) -> dict:
    record = {
        "id":          str(uuid.uuid4()),
        "action_type": action_type,
        "params":      params,
        "proposed_by": proposed_by,
        "status":      "pending",
        "created_at":  _now(),
        "updated_at":  _now(),
        "result":      None,
        "error":       None,
    }
    if _USE_SQLITE:
        with _get_conn() as conn:
            conn.execute("""
                INSERT INTO actions
                  (id, action_type, params, proposed_by, status, created_at, updated_at, result, error)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record["id"], record["action_type"],
                json.dumps(record["params"]), record["proposed_by"],
                record["status"], record["created_at"], record["updated_at"],
                None, None,
            ))
    else:
        _store[record["id"]] = record
    return record


def get_all() -> list[dict]:
    if _USE_SQLITE:
        with _get_conn() as conn:
            rows = conn.execute("SELECT * FROM actions ORDER BY created_at DESC").fetchall()
        return [_row_to_dict(r) for r in rows]
    return list(_store.values())


def get_one(action_id: str) -> dict | None:
    if _USE_SQLITE:
        with _get_conn() as conn:
            row = conn.execute("SELECT * FROM actions WHERE id = ?", (action_id,)).fetchone()
        return _row_to_dict(row) if row else None
    return _store.get(action_id)


def update_status(action_id: str, status: str, result=None, error: str = None) -> dict:
    if _USE_SQLITE:
        with _get_conn() as conn:
            conn.execute("""
                UPDATE actions
                SET status = ?, updated_at = ?, result = ?, error = ?
                WHERE id = ?
            """, (
                status, _now(),
                json.dumps(result) if result else None,
                error, action_id,
            ))
        return get_one(action_id)
    else:
        record = _store[action_id]
        record.update({"status": status, "updated_at": _now(), "result": result, "error": error})
        return record