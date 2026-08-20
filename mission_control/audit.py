"""Append-only audit chain helpers for OAP.

Provides append_event(conn, actor, action, target, metadata) and verify_audit().
"""
from __future__ import annotations

import sqlite3
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Tuple, List

from . import config

AUDIT_TABLE = "audit_events"


def _canonical_json(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def append_event(conn: sqlite3.Connection, actor: str, actor_type: str, authority_level: int, action: str, target: str, reason: Optional[str], metadata: dict, correlation_id: Optional[str] = None) -> Tuple[int, str]:
    """Append an audit event atomically with domain changes assumed to be in the same transaction.

    Returns (event_seq, curr_hash)
    """
    # Use BEGIN IMMEDIATE to serialize writers
    conn.execute("BEGIN IMMEDIATE")
    try:
        cur = conn.execute(f"SELECT event_seq, curr_hash FROM {AUDIT_TABLE} ORDER BY event_seq DESC LIMIT 1")
        row = cur.fetchone()
        prev_seq = 0
        prev_hash = ""
        if row:
            prev_seq = int(row[0])
            prev_hash = row[1]
        next_seq = prev_seq + 1

        payload = {
            "event_seq": next_seq,
            "actor": actor,
            "actor_type": actor_type,
            "authority_level": authority_level,
            "action": action,
            "target": target,
            "reason": reason,
            "metadata": metadata or {},
            "correlation_id": correlation_id,
            "timestamp": _now_iso(),
        }
        # redact sensitive fields from metadata
        redacted = _redact_metadata(payload["metadata"])
        payload["metadata"] = redacted

        canonical = _canonical_json(payload)
        curr_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()

        conn.execute(
            f"INSERT INTO {AUDIT_TABLE} (event_seq, prev_hash, curr_hash, payload, timestamp) VALUES (?,?,?,?,?)",
            (next_seq, prev_hash, curr_hash, canonical, payload["timestamp"]),
        )
        conn.execute("COMMIT")
        return next_seq, curr_hash
    except Exception:
        conn.execute("ROLLBACK")
        raise


def _redact_metadata(metadata: dict) -> dict:
    # Remove or replace sensitive keys
    keys_to_redact = {"totp_secret", "recovery_code", "password", "private_key", "secret"}
    out = {}
    for k, v in metadata.items():
        if k in keys_to_redact:
            out[k] = "<REDACTED>"
        else:
            out[k] = v
    return out


def verify_audit(db_path: Optional[str] = None) -> Tuple[bool, List[str]]:
    """Read-only verification of the audit chain. Returns (ok, report_lines)

    If db_path is None, uses config.OAP_DATABASE_PATH
    """
    if db_path is None:
        db_path = config.OAP_DATABASE_PATH
    database = Path(db_path)
    if not database.is_file():
        return False, ["Mission Control database not initialized"]

    uri = database.resolve().as_uri() + "?mode=ro"
    try:
        conn = sqlite3.connect(uri, uri=True, timeout=1)
        conn.execute("PRAGMA query_only = ON")
    except sqlite3.Error:
        return False, ["Mission Control database unavailable"]

    try:
        table = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ? LIMIT 1",
            (AUDIT_TABLE,),
        ).fetchone()
        if table is None:
            return False, ["Mission Control audit chain not initialized"]

        cur = conn.execute(f"SELECT event_seq, prev_hash, curr_hash, payload FROM {AUDIT_TABLE} ORDER BY event_seq ASC")
        prev_hash = ""
        expected_seq = 1
        problems = []
        for row in cur:
            seq, p_hash, c_hash, payload = row
            seq = int(seq)
            if seq != expected_seq:
                problems.append(f"Sequence gap: expected {expected_seq} got {seq}")
                expected_seq = seq
            # verify prev_hash matches
            if p_hash != prev_hash:
                problems.append(f"Prev_hash mismatch at seq {seq}")
            # verify hash
            h = hashlib.sha256(payload.encode("utf-8")).hexdigest()
            if h != c_hash:
                problems.append(f"Hash mismatch at seq {seq}")
            prev_hash = c_hash
            expected_seq += 1
        if problems:
            return False, problems
        return True, ["OK"]
    except sqlite3.Error:
        return False, ["Mission Control audit chain unavailable"]
    finally:
        conn.close()
