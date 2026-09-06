"""Founder-only local receipt backend for SMI Brain proof gates.

This backend gives the private War Room a bounded write/read receipt store for
SMI evidence checks. It is intentionally local-first and safe: it records proof
metadata for HRM-style receipts and Matrix learning receipts, but it does not
execute external actions, dispatch, spend, track users, self-approve, or claim a
production Neon mirror unless a separate Neon backend is configured and proved.
"""
from __future__ import annotations

import json
import os
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_DB_PATH = "/tmp/oap_smi_receipts.sqlite3"
ALLOWED_RECEIPT_KINDS = {
    "hrm_neon_evidence_receipt",
    "matrix_learning_receipt",
    "war_room_live_proof_receipt",
    "agent_tool_connection_receipt",
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _db_path() -> str:
    configured = os.getenv("OAP_SMI_RECEIPT_DB_PATH") or os.getenv("OAP_RECEIPT_DB_PATH")
    return configured or DEFAULT_DB_PATH


def _connect() -> sqlite3.Connection:
    db_path = _db_path()
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    return connection


def _init_schema(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS smi_evidence_receipts (
            receipt_id TEXT PRIMARY KEY,
            receipt_kind TEXT NOT NULL,
            brain_part TEXT NOT NULL,
            gate INTEGER NOT NULL,
            command TEXT NOT NULL,
            signal TEXT NOT NULL,
            guardian TEXT NOT NULL,
            green_gate TEXT NOT NULL,
            founder_final TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_smi_receipts_part_gate ON smi_evidence_receipts(brain_part, gate)"
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_smi_receipts_kind ON smi_evidence_receipts(receipt_kind)"
    )
    connection.commit()


def _normalise_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "brain_part": str(payload.get("brain_part") or "unknown"),
        "gate": int(payload.get("gate") or 0),
        "command": str(payload.get("command") or "war_room"),
        "signal": str(payload.get("signal") or "🟢"),
        "guardian": str(payload.get("guardian") or "required"),
        "green_gate": str(payload.get("green_gate") or "required"),
        "founder_final": str(payload.get("founder_final") or "required_for_full_green"),
        "safe_payload": dict(payload.get("safe_payload") or {}),
    }


def write_receipt(receipt_kind: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Write one bounded receipt and verify it by reading it back."""

    kind = str(receipt_kind or "").strip()
    if kind not in ALLOWED_RECEIPT_KINDS:
        return {
            "ok": False,
            "status": "blocked_unknown_receipt_kind",
            "receipt_kind": kind,
            "receipt_id": None,
            "read_back_ok": False,
        }

    normalised = _normalise_payload(payload)
    receipt_id = f"smi-{uuid.uuid4().hex}"
    created_at = _now()
    with _connect() as connection:
        _init_schema(connection)
        connection.execute(
            """
            INSERT INTO smi_evidence_receipts (
                receipt_id, receipt_kind, brain_part, gate, command, signal,
                guardian, green_gate, founder_final, payload_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                receipt_id,
                kind,
                normalised["brain_part"],
                normalised["gate"],
                normalised["command"],
                normalised["signal"],
                normalised["guardian"],
                normalised["green_gate"],
                normalised["founder_final"],
                json.dumps(normalised["safe_payload"], sort_keys=True),
                created_at,
            ),
        )
        connection.commit()
        row = connection.execute(
            "SELECT receipt_id, receipt_kind, brain_part, gate, command, created_at FROM smi_evidence_receipts WHERE receipt_id = ?",
            (receipt_id,),
        ).fetchone()

    read_back_ok = bool(row and row["receipt_id"] == receipt_id and row["receipt_kind"] == kind)
    return {
        "ok": read_back_ok,
        "status": "written_and_read_back" if read_back_ok else "write_failed_or_unreadable",
        "receipt_kind": kind,
        "receipt_id": receipt_id,
        "brain_part": normalised["brain_part"],
        "gate": normalised["gate"],
        "command": normalised["command"],
        "created_at": created_at,
        "read_back_ok": read_back_ok,
        "backend": "local_sqlite_receipt_store",
        "neon_mirror": "not_claimed_without_configured_neon_backend",
    }


def latest_receipts(limit: int = 20) -> dict[str, Any]:
    """Return recent receipts without exposing private payload contents."""

    safe_limit = max(1, min(int(limit or 20), 100))
    with _connect() as connection:
        _init_schema(connection)
        rows = connection.execute(
            """
            SELECT receipt_id, receipt_kind, brain_part, gate, command, signal,
                   guardian, green_gate, founder_final, created_at
            FROM smi_evidence_receipts
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (safe_limit,),
        ).fetchall()
    return {
        "name": "SMI Evidence Receipts",
        "backend": "local_sqlite_receipt_store",
        "count": len(rows),
        "receipts": tuple(dict(row) for row in rows),
        "neon_mirror": "not_claimed_without_configured_neon_backend",
    }


def receipt_backend_status() -> dict[str, Any]:
    """Return backend readiness and safety locks."""

    probe = write_receipt(
        "hrm_neon_evidence_receipt",
        {
            "brain_part": "receipt_backend_probe",
            "gate": 5,
            "command": "backend_status",
            "signal": "🟢",
            "safe_payload": {"probe": True, "external_action": False},
        },
    )
    return {
        "name": "SMI Receipt Backend Status",
        "local_receipt_backend": "available" if probe["ok"] else "failed",
        "local_write_read_proof": probe,
        "hrm_receipt_ready": bool(probe["ok"]),
        "matrix_learning_receipt_ready": bool(probe["ok"]),
        "neon_mirror_ready": False,
        "neon_mirror_reason": "No production Neon write/read proof is claimed by this local receipt backend.",
        "full_system_green": False,
        "locks": {
            "founder_only": True,
            "no_fake_green": True,
            "no_external_execution": True,
            "no_self_approval": True,
            "public_private_separation": True,
        },
    }
