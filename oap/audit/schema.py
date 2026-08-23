"""Canonical SQLite schema for the OAP audit chain."""

from __future__ import annotations

import sqlite3

AUDIT_REQUIRED_COLUMNS = frozenset(
    {
        "event_seq",
        "event_id",
        "prev_hash",
        "curr_hash",
        "actor_id",
        "actor_type",
        "authority_level",
        "action",
        "target",
        "reason",
        "correlation_id",
        "metadata",
        "timestamp",
    }
)

SCHEMA_STATEMENTS = (
    """
    CREATE TABLE IF NOT EXISTS audit_events (
        event_seq INTEGER PRIMARY KEY,
        event_id TEXT NOT NULL UNIQUE,
        prev_hash TEXT NOT NULL,
        curr_hash TEXT NOT NULL UNIQUE,
        actor_id TEXT NOT NULL,
        actor_type TEXT NOT NULL,
        authority_level INTEGER,
        action TEXT NOT NULL,
        target TEXT NOT NULL,
        reason TEXT NOT NULL,
        correlation_id TEXT NOT NULL,
        metadata TEXT NOT NULL,
        timestamp TEXT NOT NULL
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_audit_timestamp ON audit_events(timestamp)",
    (
        "CREATE INDEX IF NOT EXISTS ix_audit_correlation "
        "ON audit_events(correlation_id)"
    ),
    "CREATE INDEX IF NOT EXISTS ix_audit_actor ON audit_events(actor_id)",
    "CREATE INDEX IF NOT EXISTS ix_audit_action ON audit_events(action)",
    "CREATE INDEX IF NOT EXISTS ix_audit_target ON audit_events(target)",
)


def initialize_audit_schema(connection: sqlite3.Connection) -> None:
    existing = connection.execute(
        "SELECT 1 FROM sqlite_master "
        "WHERE type = 'table' AND name = 'audit_events'"
    ).fetchone()
    if existing is not None and not audit_schema_ready(connection):
        raise RuntimeError(
            "Existing audit_events table is incompatible; automatic replacement "
            "is forbidden"
        )
    for statement in SCHEMA_STATEMENTS:
        connection.execute(statement)
    if not audit_schema_ready(connection):
        raise RuntimeError("Canonical audit schema initialization failed")


def audit_schema_ready(connection: sqlite3.Connection) -> bool:
    """Return whether the canonical audit table and columns are present."""

    row = connection.execute(
        "SELECT 1 FROM sqlite_master "
        "WHERE type = 'table' AND name = 'audit_events'"
    ).fetchone()
    if row is None:
        return False
    columns = {
        str(item[1])
        for item in connection.execute("PRAGMA table_info(audit_events)").fetchall()
    }
    return AUDIT_REQUIRED_COLUMNS <= columns
