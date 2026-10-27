"""Atomic, persistent replay admission for SMI Agents HQ.

SQLite is a bounded single-host option only. Shared multi-worker production
requires an approved common database or equivalent atomic shared service.
No automatic table creation inside request handling.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path


def initialise_nonce_store(database_path: str) -> None:
    """Explicit migration/setup step; not run during message verification."""
    with sqlite3.connect(database_path, timeout=5) as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS smi_hq_agent_nonces ("
            "agent_id TEXT NOT NULL, nonce TEXT NOT NULL, "
            "accepted_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, "
            "PRIMARY KEY (agent_id, nonce))"
        )


def sqlite_atomic_replay_guard(database_path: str):
    """Return a persistent insert-if-absent guard for one trusted host.

    Must not receive its database path from an HTTP request. Fail closed on
    missing schema, locking, unavailable storage and uniqueness violations.
    """
    if not isinstance(database_path, str) or not database_path.strip():
        raise ValueError("trusted_database_path_required")
    path = Path(database_path)
    if not path.is_file():
        raise FileNotFoundError("nonce_database_must_be_preprovisioned")

    def admit(agent_id: str, nonce: str) -> bool:
        if not isinstance(agent_id, str) or not agent_id:
            return False
        if not isinstance(nonce, str) or not nonce:
            return False
        try:
            with sqlite3.connect(
                f"file:{path.resolve()}?mode=rw", uri=True, timeout=5,
            ) as conn:
                conn.execute(
                    "INSERT INTO smi_hq_agent_nonces (agent_id, nonce) VALUES (?, ?)",
                    (agent_id, nonce),
                )
            return True
        except (sqlite3.Error, OSError):
            return False

    return admit
