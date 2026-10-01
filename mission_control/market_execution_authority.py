"""Governed unlock gate for consequential Market execution edges.

This module replaces permanent hard-coded dead ends with a durable authority gate.
It does not itself capture money, transfer funds, hand parcels to carriers, fulfil
externally, or dispatch workers. It only records evidence-backed authority and
moves existing first-party intents to READY when the required authority exists.

Provider execution remains separate and must be performed by an approved adapter.
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from . import postgres_db

MARKET_EXECUTION_AUTHORITY_MIGRATION_VERSION = "0008_market_execution_authority"

CAPABILITIES = frozenset({
    "PAYMENT_CAPTURE",
    "MONEY_TRANSFER",
    "EXTERNAL_FULFILMENT",
    "CARRIER_HANDOFF",
    "AUTOMATIC_DISPATCH",
})
AUTHORITY_STATES = frozenset({"PENDING", "APPROVED", "REVOKED", "EXPIRED"})

SCHEMA_STATEMENTS = (
    """CREATE TABLE IF NOT EXISTS oap_market_execution_authorities (
        authority_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        capability TEXT NOT NULL CHECK (capability IN (
            'PAYMENT_CAPTURE','MONEY_TRANSFER','EXTERNAL_FULFILMENT',
            'CARRIER_HANDOFF','AUTOMATIC_DISPATCH')),
        provider_name TEXT NOT NULL,
        provider_reference TEXT NOT NULL,
        evidence_sha256 TEXT NOT NULL CHECK (char_length(evidence_sha256)=64),
        human_approval_reference TEXT NOT NULL,
        state TEXT NOT NULL DEFAULT 'PENDING'
            CHECK (state IN ('PENDING','APPROVED','REVOKED','EXPIRED')),
        valid_from TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        expires_at TIMESTAMPTZ,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(capability,provider_reference))""",
    """CREATE INDEX IF NOT EXISTS ix_market_execution_authority_capability
       ON oap_market_execution_authorities(capability,state,valid_from DESC)""",
)

MIGRATION_CHECKSUM = hashlib.sha256("\n".join(SCHEMA_STATEMENTS).encode()).hexdigest()


def _capability(value: object) -> str:
    capability = str(value or "").strip().upper()
    if capability not in CAPABILITIES:
        raise ValueError("invalid_market_execution_capability")
    return capability


def _text(value: object, name: str, maximum: int = 240) -> str:
    text = " ".join(str(value or "").strip().split())
    if not text:
        raise ValueError(f"{name}_required")
    if len(text) > maximum:
        raise ValueError(f"{name}_too_long")
    return text


def _sha256(value: object) -> str:
    text = str(value or "").strip().lower()
    if len(text) != 64 or any(ch not in "0123456789abcdef" for ch in text):
        raise ValueError("invalid_evidence_sha256")
    return text


def _uuid(value: object, name: str) -> str:
    try:
        return str(UUID(str(value)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError(f"invalid_{name}") from exc


def execution_allowed(*, authority_state: str, stop_state: str, recovery_state: str) -> bool:
    """Only approved authority plus clear STOP/recovery can unlock execution."""
    if authority_state != "APPROVED":
        return False
    if stop_state not in {"NONE", "CLEARED_BY_HUMAN"}:
        return False
    return recovery_state in {"NONE", "RECOVERED"}


class MarketExecutionAuthorityStore:
    def record_authority(
        self,
        *,
        capability: object,
        provider_name: object,
        provider_reference: object,
        evidence_sha256: object,
        human_approval_reference: object,
        state: object = "APPROVED",
        expires_at: datetime | None = None,
    ) -> dict[str, Any]:
        cap = _capability(capability)
        provider = _text(provider_name, "provider_name", 120)
        reference = _text(provider_reference, "provider_reference")
        evidence = _sha256(evidence_sha256)
        approval = _text(human_approval_reference, "human_approval_reference")
        authority_state = str(state or "").strip().upper()
        if authority_state not in AUTHORITY_STATES:
            raise ValueError("invalid_authority_state")
        if expires_at is not None and expires_at.tzinfo is None:
            raise ValueError("expires_at_timezone_required")
        with postgres_db.connect() as connection:
            row = connection.execute(
                """INSERT INTO oap_market_execution_authorities(
                       capability,provider_name,provider_reference,evidence_sha256,
                       human_approval_reference,state,expires_at)
                   VALUES (%s,%s,%s,%s,%s,%s,%s)
                   ON CONFLICT (capability,provider_reference) DO UPDATE SET
                       provider_name=EXCLUDED.provider_name,
                       evidence_sha256=EXCLUDED.evidence_sha256,
                       human_approval_reference=EXCLUDED.human_approval_reference,
                       state=EXCLUDED.state,
                       expires_at=EXCLUDED.expires_at,
                       updated_at=CURRENT_TIMESTAMP
                   RETURNING authority_id,capability,provider_name,provider_reference,
                             evidence_sha256,human_approval_reference,state,
                             valid_from,expires_at,updated_at""",
                (cap, provider, reference, evidence, approval, authority_state, expires_at),
            ).fetchone()
            connection.commit()
        return _authority_row(row)

    def status(self, *, capability: object) -> dict[str, Any]:
        cap = _capability(capability)
        with postgres_db.connect(readonly=True) as connection:
            row = connection.execute(
                """SELECT authority_id,capability,provider_name,provider_reference,
                          evidence_sha256,human_approval_reference,state,
                          valid_from,expires_at,updated_at
                   FROM oap_market_execution_authorities
                   WHERE capability=%s
                   ORDER BY CASE state WHEN 'APPROVED' THEN 0 ELSE 1 END,
                            updated_at DESC
                   LIMIT 1""",
                (cap,),
            ).fetchone()
        if row is None:
            return {
                "capability": cap,
                "authority_present": False,
                "authority_ready": False,
                "execution_performed": False,
                "human_authority_final": True,
            }
        result = _authority_row(row)
        now = datetime.now(timezone.utc)
        expired = result["expires_at"] is not None and datetime.fromisoformat(result["expires_at"]) <= now
        result["authority_present"] = True
        result["authority_ready"] = result["state"] == "APPROVED" and not expired
        result["execution_performed"] = False
        result["human_authority_final"] = True
        return result

    def prepare_commerce_order(
        self, *, order_id: object, actor_identity_id: object
    ) -> dict[str, Any]:
        order = _uuid(order_id, "order_id")
        actor = _uuid(actor_identity_id, "actor_identity_id")
        payment = self.status(capability="PAYMENT_CAPTURE")
        fulfilment = self.status(capability="EXTERNAL_FULFILMENT")
        with postgres_db.connect() as connection:
            owned = connection.execute(
                """SELECT buyer_identity_id,seller_identity_id,state
                   FROM oap_commerce_orders WHERE order_id=%s FOR UPDATE""",
                (order,),
            ).fetchone()
            if owned is None or actor not in {str(owned[0]), str(owned[1])}:
                raise PermissionError("order_not_owned")
            payment_state = "READY" if payment["authority_ready"] else "PROVIDER_REQUIRED"
            fulfilment_state = "READY" if fulfilment["authority_ready"] else "PROVIDER_REQUIRED"
            connection.execute(
                """UPDATE oap_commerce_payment_intents
                   SET state=%s,provider_reference=%s,updated_at=CURRENT_TIMESTAMP
                   WHERE order_id=%s AND state='PROVIDER_REQUIRED'""",
                (payment_state, payment.get("provider_reference"), order),
            )
            connection.execute(
                """UPDATE oap_commerce_fulfilment_intents
                   SET state=%s,provider_reference=%s,updated_at=CURRENT_TIMESTAMP
                   WHERE order_id=%s AND state='PROVIDER_REQUIRED'""",
                (fulfilment_state, fulfilment.get("provider_reference"), order),
            )
            connection.commit()
        return {
            "order_id": order,
            "payment_intent_ready": payment_state == "READY",
            "fulfilment_intent_ready": fulfilment_state == "READY",
            "payment_capture_performed": False,
            "money_transfer_performed": False,
            "external_fulfilment_performed": False,
            "provider_execution_required": True,
            "human_authority_final": True,
        }


def _authority_row(row: Any) -> dict[str, Any]:
    return {
        "authority_id": str(row[0]),
        "capability": str(row[1]),
        "provider_name": str(row[2]),
        "provider_reference": str(row[3]),
        "evidence_sha256": str(row[4]),
        "human_approval_reference": str(row[5]),
        "state": str(row[6]),
        "valid_from": row[7].isoformat(),
        "expires_at": row[8].isoformat() if row[8] else None,
        "updated_at": row[9].isoformat(),
    }


def migration_sql() -> str:
    statements = list(SCHEMA_STATEMENTS)
    statements.append(
        "INSERT INTO oap_schema_migrations(version,checksum) "
        f"VALUES ('{MARKET_EXECUTION_AUTHORITY_MIGRATION_VERSION}','{MIGRATION_CHECKSUM}') "
        "ON CONFLICT (version) DO NOTHING"
    )
    return ";\n\n".join(statements) + ";\n"


STORE = MarketExecutionAuthorityStore()
