"""Append-only, hash-chained audit implementation."""

from __future__ import annotations

import hashlib
import hmac
import json
import sqlite3
from pathlib import Path
from typing import Any
from uuid import uuid4

from oap.contracts import utc_now

AUDIT_TABLE = "audit_events"
_AUDIT_COLUMNS = (
    "event_seq",
    "event_id",
    "prev_hash",
    "actor_id",
    "actor_type",
    "authority_level",
    "action",
    "target",
    "reason",
    "correlation_id",
    "metadata",
    "timestamp",
)
_SENSITIVE_KEYS = {
    "password",
    "private_key",
    "recovery_code",
    "secret",
    "token",
    "totp",
    "totp_secret",
}


def _canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def _redact(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            str(key): "<REDACTED>"
            if str(key).casefold() in _SENSITIVE_KEYS
            else _redact(item)
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [_redact(item) for item in value]
    return value


def _hash_payload(payload: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def append_event(
    connection: sqlite3.Connection,
    actor: str,
    actor_type: str,
    authority_level: int | None,
    action: str,
    target: str,
    reason: str | None,
    metadata: dict[str, Any] | None,
    correlation_id: str | None = None,
) -> tuple[int, str]:
    """Append one redacted event and return ``(sequence, current_hash)``."""

    started_transaction = not connection.in_transaction
    if started_transaction:
        connection.execute("BEGIN IMMEDIATE")
    try:
        row = connection.execute(
            f"SELECT event_seq, curr_hash FROM {AUDIT_TABLE} "
            "ORDER BY event_seq DESC LIMIT 1"
        ).fetchone()
        sequence = int(row[0]) + 1 if row else 1
        previous_hash = str(row[1]) if row else ""
        payload = {
            "event_seq": sequence,
            "event_id": str(uuid4()),
            "prev_hash": previous_hash,
            "actor_id": actor,
            "actor_type": actor_type,
            "authority_level": authority_level,
            "action": action,
            "target": target,
            "reason": reason or "",
            "correlation_id": correlation_id or str(uuid4()),
            "metadata": _redact(metadata or {}),
            "timestamp": utc_now().isoformat(),
        }
        current_hash = _hash_payload(payload)
        connection.execute(
            f"INSERT INTO {AUDIT_TABLE} ("
            "event_seq, event_id, prev_hash, curr_hash, actor_id, actor_type, "
            "authority_level, action, target, reason, correlation_id, metadata, "
            "timestamp"
            ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                payload["event_seq"],
                payload["event_id"],
                payload["prev_hash"],
                current_hash,
                payload["actor_id"],
                payload["actor_type"],
                payload["authority_level"],
                payload["action"],
                payload["target"],
                payload["reason"],
                payload["correlation_id"],
                _canonical_json(payload["metadata"]),
                payload["timestamp"],
            ),
        )
        if started_transaction:
            connection.execute("COMMIT")
        return sequence, current_hash
    except Exception:
        if started_transaction:
            connection.execute("ROLLBACK")
        raise


def verify_audit_path(db_path: str | Path) -> tuple[bool, list[str]]:
    """Verify sequence and hashes without opening a writable connection."""

    database = Path(db_path)
    if not database.is_file():
        return False, ["Mission Control database not initialized"]
    try:
        connection = sqlite3.connect(
            database.resolve().as_uri() + "?mode=ro",
            uri=True,
            timeout=1,
        )
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA query_only = ON")
    except sqlite3.Error:
        return False, ["Mission Control database unavailable"]

    try:
        exists = connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
            (AUDIT_TABLE,),
        ).fetchone()
        if exists is None:
            return False, ["Mission Control audit chain not initialized"]
        columns = {
            str(row["name"])
            for row in connection.execute(f"PRAGMA table_info({AUDIT_TABLE})")
        }
        required = {*_AUDIT_COLUMNS, "curr_hash"}
        if not required <= columns:
            return False, ["Mission Control audit schema is incompatible"]

        rows = connection.execute(
            f"SELECT {', '.join(_AUDIT_COLUMNS)}, curr_hash FROM {AUDIT_TABLE} "
            "ORDER BY event_seq"
        ).fetchall()
        previous_hash = ""
        problems: list[str] = []
        for expected_sequence, row in enumerate(rows, start=1):
            sequence = int(row["event_seq"])
            if sequence != expected_sequence:
                problems.append(
                    f"Sequence gap: expected {expected_sequence} got {sequence}"
                )
            if str(row["prev_hash"]) != previous_hash:
                problems.append(f"Previous hash mismatch at sequence {sequence}")
            try:
                metadata = json.loads(str(row["metadata"]))
            except json.JSONDecodeError:
                problems.append(f"Invalid metadata JSON at sequence {sequence}")
                metadata = {}
            payload = {
                column: metadata if column == "metadata" else row[column]
                for column in _AUDIT_COLUMNS
            }
            expected_hash = _hash_payload(payload)
            current_hash = str(row["curr_hash"])
            if not hmac.compare_digest(expected_hash, current_hash):
                problems.append(f"Hash mismatch at sequence {sequence}")
            previous_hash = current_hash
        return (False, problems) if problems else (True, ["OK"])
    except sqlite3.Error:
        return False, ["Mission Control audit chain unavailable"]
    finally:
        connection.close()
