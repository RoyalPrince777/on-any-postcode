"""SQLite-backed SMI governance audit trail; no execution or approval authority.

Append-only application interface with transactional chain checks. A database
administrator can still alter or replace this file: external anchoring, backups,
access control and authenticated approvals are required for stronger assurance.
"""
from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict
from hashlib import sha256
from pathlib import Path

from oap.smi.governance_decision_registry import DecisionRecord


def _canonical(value: dict) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _validate_record(record: dict, previous: str | None) -> None:
    digest = record.get("record_hash")
    payload = {key: value for key, value in record.items() if key != "record_hash"}
    if digest != sha256(_canonical(payload).encode()).hexdigest():
        raise ValueError("decision record hash mismatch")
    if record.get("previous_record_hash") != previous:
        raise ValueError("broken governance audit chain")
    if record.get("execution_status") != "NOT_AUTHORISED":
        raise ValueError("registry cannot grant execution authority")


class GovernanceAuditStore:
    """Single-file, serialised SQLite audit trail for one local writer domain."""

    def __init__(self, path: str | Path) -> None:
        self.path = str(path)
        with sqlite3.connect(self.path, timeout=10) as db:
            db.execute(
                "CREATE TABLE IF NOT EXISTS governance_audit ("
                "sequence INTEGER PRIMARY KEY AUTOINCREMENT,"
                "decision_id TEXT NOT NULL UNIQUE,"
                "payload TEXT NOT NULL)"
            )

    @staticmethod
    def _verify(db: sqlite3.Connection) -> tuple[list[dict], str | None]:
        records = []
        previous = None
        for (payload,) in db.execute(
            "SELECT payload FROM governance_audit ORDER BY sequence"
        ):
            record = json.loads(payload)
            _validate_record(record, previous)
            records.append(record)
            previous = record["record_hash"]
        return records, previous

    def verify(self) -> tuple[dict, ...]:
        with sqlite3.connect(self.path, timeout=10) as db:
            records, _ = self._verify(db)
        return tuple(records)

    def append(self, record: DecisionRecord) -> None:
        """Atomically verify existing history and append exactly one record."""
        with sqlite3.connect(self.path, timeout=10) as db:
            db.execute("BEGIN IMMEDIATE")
            _, previous = self._verify(db)
            payload = asdict(record)
            _validate_record(payload, previous)
            db.execute(
                "INSERT INTO governance_audit (decision_id, payload) VALUES (?, ?)",
                (record.decision_id, _canonical(payload)),
            )
