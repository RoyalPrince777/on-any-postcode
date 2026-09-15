"""Bounded durable HRM receipt persistence for governed OAP Signals.

Writes are opt-in, additive, idempotent and fail closed. The caller must supply
complete 7-7-7 proof and any required Human Authority approval before a receipt
can be persisted. Secrets are never returned.
"""
from __future__ import annotations

import hashlib
import json
import os
import uuid
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from mission_control.hrm_readonly_probe import _database_config, _ssl_url

_REQUIRED_PLANES = ("mind", "body", "soul")
_REQUIRED_COUNTS = {"mind": 7, "body": 7, "soul": 7}


class ReceiptBlocked(RuntimeError):
    """Governance rejected a durable receipt write."""


@dataclass(frozen=True)
class DurableReceipt:
    receipt_id: str
    checksum: str
    payload: dict[str, Any]


def _canonical(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _checksum(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(_canonical(payload).encode("utf-8")).hexdigest()


def _validate(payload: Mapping[str, Any]) -> None:
    if payload.get("governance") != "7-7-7":
        raise ReceiptBlocked("canonical_governance_required")
    checks = payload.get("checks")
    if not isinstance(checks, Mapping):
        raise ReceiptBlocked("governance_checks_required")
    for plane in _REQUIRED_PLANES:
        values = checks.get(plane)
        if not isinstance(values, Mapping) or len(values) != _REQUIRED_COUNTS[plane]:
            raise ReceiptBlocked(f"{plane}_seven_checks_required")
        if not all(value is True for value in values.values()):
            raise ReceiptBlocked(f"{plane}_proof_incomplete")
    if payload.get("evidence_proven") is not True:
        raise ReceiptBlocked("evidence_required")
    if payload.get("authority_transferred") is not False:
        raise ReceiptBlocked("authority_escalation_forbidden")
    if payload.get("human_authority_required") is True and payload.get("human_authority_approved") is not True:
        raise ReceiptBlocked("human_authority_required")


def build_receipt(signal_id: str, payload: Mapping[str, Any]) -> DurableReceipt:
    _validate(payload)
    body = dict(payload)
    body["signal_id"] = str(signal_id)
    body["recorded_at"] = datetime.now(timezone.utc).isoformat()
    checksum = _checksum(body)
    receipt_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"oap-hrm:{signal_id}:{checksum}"))
    return DurableReceipt(receipt_id=receipt_id, checksum=checksum, payload=body)


def persist_and_read_back(receipt: DurableReceipt) -> dict[str, Any]:
    if os.environ.get("OAP_HRM_DURABLE_WRITES_ENABLED", "").strip().lower() not in {"1", "true", "yes"}:
        raise ReceiptBlocked("durable_writes_disabled")
    database_url, _source = _database_config()
    if not database_url:
        raise ReceiptBlocked("hrm_database_unconfigured")

    import psycopg
    from psycopg.types.json import Jsonb

    with psycopg.connect(_ssl_url(database_url), connect_timeout=5, application_name="oap-hrm-durable-receipt") as connection:
        with connection.transaction():
            connection.execute(
                """CREATE TABLE IF NOT EXISTS oap_hrm_receipts (
                    receipt_id UUID PRIMARY KEY,
                    signal_id TEXT NOT NULL,
                    checksum CHAR(64) NOT NULL,
                    payload JSONB NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    UNIQUE(signal_id, checksum)
                )"""
            )
            connection.execute(
                """INSERT INTO oap_hrm_receipts(receipt_id, signal_id, checksum, payload)
                   VALUES (%s, %s, %s, %s)
                   ON CONFLICT (receipt_id) DO NOTHING""",
                (receipt.receipt_id, receipt.payload["signal_id"], receipt.checksum, Jsonb(receipt.payload)),
            )
            row = connection.execute(
                "SELECT receipt_id::text, checksum, payload FROM oap_hrm_receipts WHERE receipt_id = %s",
                (receipt.receipt_id,),
            ).fetchone()
            if row is None or row[1] != receipt.checksum or _checksum(row[2]) != receipt.checksum:
                raise ReceiptBlocked("receipt_readback_verification_failed")
        return {"receipt_id": row[0], "checksum": row[1], "write_verified": True, "read_back_verified": True, "authority_transferred": False, "secret_exposed": False}
