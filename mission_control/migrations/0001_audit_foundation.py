"""Initial migration: 0001_audit_foundation

Creates schema_migrations and audit_events with fields and indexes required.
"""
from __future__ import annotations

from typing import Any
from datetime import datetime, timezone


def migrate(conn):
    # Create schema_migrations and audit_events as the bootstrap schema
    conn.execute("BEGIN IMMEDIATE")
    try:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS schema_migrations (version TEXT PRIMARY KEY, name TEXT, checksum TEXT, applied_at TEXT)"
        )

        conn.execute(
            "CREATE TABLE IF NOT EXISTS audit_events (\n"
            " event_seq INTEGER PRIMARY KEY,\n"
            " event_id TEXT NOT NULL UNIQUE,\n"
            " prev_hash TEXT NOT NULL,\n"
            " curr_hash TEXT NOT NULL UNIQUE,\n"
            " actor_id TEXT NOT NULL,\n"
            " actor_type TEXT NOT NULL,\n"
            " authority_level INTEGER,\n"
            " action TEXT NOT NULL,\n"
            " target TEXT NOT NULL,\n"
            " reason TEXT NOT NULL,\n"
            " correlation_id TEXT NOT NULL,\n"
            " metadata TEXT NOT NULL,\n"
            " timestamp TEXT NOT NULL\n"
            ")"
        )

        # Indexes
        conn.execute("CREATE INDEX IF NOT EXISTS ix_audit_timestamp ON audit_events(timestamp)")
        conn.execute(
            "CREATE INDEX IF NOT EXISTS ix_audit_correlation ON audit_events(correlation_id)"
        )
        conn.execute("CREATE INDEX IF NOT EXISTS ix_audit_actor ON audit_events(actor_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS ix_audit_action ON audit_events(action)")
        conn.execute("CREATE INDEX IF NOT EXISTS ix_audit_target ON audit_events(target)")

        conn.execute("COMMIT")
    except Exception:
        conn.execute("ROLLBACK")
        raise
