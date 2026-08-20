"""Explicit SQLite schema for SMI-owned HRM records and world state."""

from __future__ import annotations

import sqlite3

BRAIN_REQUIRED_COLUMNS = {
    "smi_memory_records": frozenset(
        {
            "memory_id",
            "request_id",
            "identity_id",
            "task_type",
            "content_hash",
            "summary",
            "output_state",
            "signal_level",
            "rationale_json",
            "processing_states_json",
            "created_at",
        }
    ),
    "smi_approval_receipts": frozenset(
        {
            "receipt_id",
            "request_id",
            "identity_id",
            "decision",
            "issued_at",
            "expires_at",
            "action_digest",
            "consumed_at",
        }
    ),
    "smi_kernel_outcomes": frozenset(
        {
            "outcome_id",
            "request_id",
            "state",
            "executed",
            "reason",
            "approval_receipt_id",
            "created_at",
        }
    ),
    "smi_world_state": frozenset(
        {
            "state_key",
            "value_json",
            "version",
            "approval_receipt_id",
            "updated_at",
        }
    ),
}

SCHEMA_STATEMENTS = (
    """
    CREATE TABLE IF NOT EXISTS smi_memory_records (
        memory_id TEXT PRIMARY KEY,
        request_id TEXT NOT NULL UNIQUE,
        identity_id TEXT NOT NULL,
        task_type TEXT NOT NULL,
        content_hash TEXT NOT NULL,
        summary TEXT NOT NULL,
        output_state TEXT NOT NULL,
        signal_level TEXT NOT NULL,
        rationale_json TEXT NOT NULL,
        processing_states_json TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS ix_smi_memory_task_created
    ON smi_memory_records(task_type, created_at DESC)
    """,
    """
    CREATE TABLE IF NOT EXISTS smi_approval_receipts (
        receipt_id TEXT PRIMARY KEY,
        request_id TEXT NOT NULL UNIQUE,
        identity_id TEXT NOT NULL,
        decision TEXT NOT NULL CHECK (decision IN ('APPROVED', 'REJECTED')),
        issued_at TEXT NOT NULL,
        expires_at TEXT NOT NULL,
        action_digest TEXT NOT NULL,
        consumed_at TEXT NOT NULL
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS ix_smi_approval_identity_consumed
    ON smi_approval_receipts(identity_id, consumed_at DESC)
    """,
    """
    CREATE TABLE IF NOT EXISTS smi_kernel_outcomes (
        outcome_id TEXT PRIMARY KEY,
        request_id TEXT NOT NULL,
        state TEXT NOT NULL,
        executed INTEGER NOT NULL CHECK (executed IN (0, 1)),
        reason TEXT NOT NULL,
        approval_receipt_id TEXT,
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS ix_smi_outcome_request_created
    ON smi_kernel_outcomes(request_id, created_at DESC)
    """,
    """
    CREATE TABLE IF NOT EXISTS smi_world_state (
        state_key TEXT PRIMARY KEY,
        value_json TEXT NOT NULL,
        version INTEGER NOT NULL CHECK (version > 0),
        approval_receipt_id TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """,
)


def initialize_brain_schema(connection: sqlite3.Connection) -> None:
    """Create only SMI-owned tables inside an explicitly managed connection."""

    for table, required_columns in BRAIN_REQUIRED_COLUMNS.items():
        if _table_exists(connection, table) and not _table_has_columns(
            connection,
            table,
            required_columns,
        ):
            raise RuntimeError(
                f"Existing {table} table is incompatible; automatic replacement "
                "is forbidden"
            )
    for statement in SCHEMA_STATEMENTS:
        connection.execute(statement)
    if not brain_schema_ready(connection):
        raise RuntimeError("Canonical SMI brain schema initialization failed")


def brain_schema_ready(connection: sqlite3.Connection) -> bool:
    """Return whether every canonical SMI-owned table and column is present."""

    return all(
        _table_has_columns(connection, table, columns)
        for table, columns in BRAIN_REQUIRED_COLUMNS.items()
    )


def _table_exists(connection: sqlite3.Connection, table: str) -> bool:
    return (
        connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
            (table,),
        ).fetchone()
        is not None
    )


def _table_has_columns(
    connection: sqlite3.Connection,
    table: str,
    required: frozenset[str],
) -> bool:
    if not _table_exists(connection, table):
        return False
    columns = {
        str(row[1])
        for row in connection.execute(f"PRAGMA table_info({table})").fetchall()
    }
    return required <= columns
