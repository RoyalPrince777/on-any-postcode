"""Bounded durable HRM receipt persistence for governed OAP Signals.

Writes are opt-in and fail closed. Runtime persistence never mutates schema.
The caller supplies complete canonical 7-7-7 proof and Human Authority approval
when required. Secrets are never returned.
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

from mission_control.hrm_agent_lifecycle import BODY_7, MIND_7, SOUL_7
from mission_control.hrm_readonly_probe import _database_config, _ssl_url

_REQUIRED_CHECKS = {
    "mind": frozenset(MIND_7),
    "body": frozenset(BODY_7),
    "soul": frozenset(SOUL_7),
}


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
    if not isinstance(checks, Mapping) or set(checks) != set(_REQUIRED_CHECKS):
        raise ReceiptBlocked("canonical_governance_checks_required")
    for plane, required in _REQUIRED_CHECKS.items():
        values = checks.get(plane)
        if not isinstance(values, Mapping) or set(values) != required:
            raise ReceiptBlocked(f"{plane}_canonical_checks_required")
        if not all(values[name] is True for name in required):
            raise ReceiptBlocked(f"{plane}_proof_incomplete")
    if payload.get("evidence_proven") is not True:
        raise ReceiptBlocked("evidence_required")
    if payload.get("authority_transferred") is not False:
        raise ReceiptBlocked("authority_escalation_forbidden")
    if (
        payload.get("human_authority_required") is True
        and payload.get("human_authority_approved") is not True
    ):
        raise ReceiptBlocked("human_authority_required")


def build_receipt(
    signal_id: str, payload: Mapping[str, Any], *, idempotency_key: str
) -> DurableReceipt:
    _validate(payload)
    signal_id = str(signal_id).strip()
    idempotency_key = str(idempotency_key).strip()
    if not signal_id:
        raise ReceiptBlocked("signal_id_required")
    if not idempotency_key:
        raise ReceiptBlocked("idempotency_key_required")

    governed = dict(payload)
    governed["signal_id"] = signal_id
    governed["idempotency_key"] = idempotency_key
    checksum = _checksum(governed)
    receipt_id = str(
        uuid.uuid5(uuid.NAMESPACE_URL, f"oap-hrm:{signal_id}:{idempotency_key}")
    )
    body = dict(governed)
    body["recorded_at"] = datetime.now(timezone.utc).isoformat()
    return DurableReceipt(receipt_id=receipt_id, checksum=checksum, payload=body)


def persist_and_read_back(receipt: DurableReceipt) -> dict[str, Any]:
    if os.environ.get("OAP_HRM_DURABLE_WRITES_ENABLED", "").strip().lower() not in {
        "1",
        "true",
        "yes",
    }:
        raise ReceiptBlocked("durable_writes_disabled")
    database_url, _source = _database_config()
    if not database_url:
        raise ReceiptBlocked("hrm_database_unconfigured")

    import psycopg
    from psycopg.types.json import Jsonb

    try:
        with (
            psycopg.connect(
                _ssl_url(database_url),
                connect_timeout=5,
                application_name="oap-hrm-durable-receipt",
            ) as connection,
            connection.transaction(),
        ):
            row = connection.execute(
                "SELECT receipt_id::text, checksum, payload FROM oap_hrm_receipts WHERE receipt_id = %s",
                (receipt.receipt_id,),
            ).fetchone()
            if row is None:
                connection.execute(
                    """INSERT INTO oap_hrm_receipts(receipt_id, signal_id, checksum, payload)
                       VALUES (%s, %s, %s, %s)
                       ON CONFLICT (receipt_id) DO NOTHING""",
                    (
                        receipt.receipt_id,
                        receipt.payload["signal_id"],
                        receipt.checksum,
                        Jsonb(receipt.payload),
                    ),
                )
                row = connection.execute(
                    "SELECT receipt_id::text, checksum, payload FROM oap_hrm_receipts WHERE receipt_id = %s",
                    (receipt.receipt_id,),
                ).fetchone()
            if (
                row is None
                or row[1] != receipt.checksum
                or _checksum(_without_recorded_at(row[2])) != receipt.checksum
            ):
                raise ReceiptBlocked("receipt_readback_verification_failed")
    except ReceiptBlocked:
        raise
    except Exception as exc:
        raise ReceiptBlocked("receipt_database_unavailable_or_schema_missing") from exc

    return {
        "receipt_id": row[0],
        "checksum": row[1],
        "write_verified": True,
        "read_back_verified": True,
        "authority_transferred": False,
        "secret_exposed": False,
    }


def _without_recorded_at(payload: Mapping[str, Any]) -> dict[str, Any]:
    body = dict(payload)
    body.pop("recorded_at", None)
    return body
