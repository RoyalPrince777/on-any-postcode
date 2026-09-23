"""Durable Raffles STOP/recovery using canonical SQLite audit atomically.

Explicit schema only; no boot-time migration. Does not open entries or release.
A caller must supply the canonical authenticated authority check for recovery.
"""
from __future__ import annotations

import sqlite3
from collections.abc import Callable

from oap.audit import append_event, audit_schema_ready

SCHEMA = (
    "CREATE TABLE IF NOT EXISTS raffles_stop_state ("
    "campaign_id TEXT PRIMARY KEY,"
    "stopped INTEGER NOT NULL DEFAULT 1 CHECK(stopped IN (0,1)),"
    "revision INTEGER NOT NULL DEFAULT 0)"
)


def initialize_schema(connection: sqlite3.Connection) -> None:
    if not audit_schema_ready(connection):
        raise RuntimeError("canonical_audit_schema_required")
    connection.execute(SCHEMA)


def status(connection: sqlite3.Connection, campaign_id: str) -> dict[str, object]:
    if not audit_schema_ready(connection) or not campaign_id:
        raise RuntimeError("raffles_stop_not_ready")
    row = connection.execute(
        "SELECT stopped,revision FROM raffles_stop_state WHERE campaign_id=?",
        (campaign_id,),
    ).fetchone()
    # Missing campaign state is NOT interpreted as permission to execute.
    return {"campaign_id": campaign_id, "stopped": True if row is None else bool(row[0]),
            "revision": 0 if row is None else int(row[1]),
            "execution_granted": False}


def set_stop(connection: sqlite3.Connection, *, campaign_id: str,
             actor: str, action: str,
             authority_checker: Callable[[str], bool] | None = None) -> dict[str, object]:
    if action not in ("STOP", "RECOVER") or not campaign_id or len(campaign_id) > 96 or not actor:
        raise ValueError("invalid_raffles_stop_command")
    if not audit_schema_ready(connection):
        raise RuntimeError("canonical_audit_schema_required")
    if action == "RECOVER" and (
        authority_checker is None or authority_checker(actor) is not True
    ):
        raise PermissionError("canonical_founder_authority_required")
    if connection.in_transaction:
        raise RuntimeError("exclusive_raffles_transaction_required")
    connection.execute("BEGIN IMMEDIATE")
    try:
        row = connection.execute(
            "SELECT revision FROM raffles_stop_state WHERE campaign_id=?",
            (campaign_id,),
        ).fetchone()
        revision = 1 if row is None else int(row[0]) + 1
        stopped = action == "STOP"
        connection.execute(
            "INSERT INTO raffles_stop_state(campaign_id,stopped,revision)"
            " VALUES(?,?,?) ON CONFLICT(campaign_id) DO UPDATE SET"
            " stopped=excluded.stopped,revision=excluded.revision",
            (campaign_id, int(stopped), revision))
        receipt = append_event(connection, actor, "HUMAN", 0 if action == "RECOVER" else None,
                               "RAFFLES_" + action, campaign_id,
                               "REVIEW_ONLY_NO_EXECUTION",
                               {"stopped": stopped, "revision": revision})
        if not isinstance(receipt, tuple) or len(receipt) != 2 or not receipt[1]:
            raise RuntimeError("canonical_audit_unconfirmed")
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    return {"campaign_id": campaign_id, "outcome": "STOPPED" if stopped else "RECOVERED_TO_REVIEW",
            "stopped": stopped, "revision": revision, "receipt_seq": receipt[0],
            "execution_granted": False, "release_allowed": False}
