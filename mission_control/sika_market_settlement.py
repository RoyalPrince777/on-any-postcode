"""SIKA-first settlement spine for OAP Market.

Canonical payment route:
Market order -> SIKA settlement intent -> approved bank/provider rail -> receipt.

This module is an orchestration and evidence layer. It does not issue SIKA,
hold deposits, execute bank transfers, calculate live FX, or capture payment.
Those actions remain behind approved regulated adapters and customer authority.
"""
from __future__ import annotations

import hashlib
import re
from typing import Any
from uuid import UUID

from . import postgres_db, market_execution_authority

SIKA_MARKET_SETTLEMENT_MIGRATION_VERSION = "0009_sika_market_settlement"
_IDEMPOTENCY = re.compile(r"^[A-Za-z0-9._:-]{8,160}$")

SETTLEMENT_STATES = frozenset({
    "BANK_AUTHORITY_REQUIRED",
    "READY_FOR_BANK",
    "SUBMITTED",
    "SETTLED",
    "FAILED",
    "STOPPED",
    "RECOVERY_REQUIRED",
})

SCHEMA_STATEMENTS = (
    """CREATE TABLE IF NOT EXISTS oap_sika_market_settlement_intents (
        settlement_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        order_id UUID NOT NULL UNIQUE REFERENCES oap_commerce_orders(order_id)
            ON DELETE RESTRICT,
        payment_intent_id UUID NOT NULL UNIQUE REFERENCES oap_commerce_payment_intents(intent_id)
            ON DELETE RESTRICT,
        buyer_identity_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
        seller_identity_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
        amount_minor BIGINT NOT NULL CHECK (amount_minor >= 0),
        settlement_currency TEXT NOT NULL,
        sika_route TEXT NOT NULL DEFAULT 'SIKA'
            CHECK (sika_route='SIKA'),
        state TEXT NOT NULL DEFAULT 'BANK_AUTHORITY_REQUIRED'
            CHECK (state IN ('BANK_AUTHORITY_REQUIRED','READY_FOR_BANK','SUBMITTED',
                             'SETTLED','FAILED','STOPPED','RECOVERY_REQUIRED')),
        bank_provider_reference TEXT,
        customer_approval_reference TEXT,
        external_receipt_reference TEXT,
        idempotency_key TEXT NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(buyer_identity_id,idempotency_key))""",
    """CREATE TABLE IF NOT EXISTS oap_sika_market_settlement_events (
        event_id BIGSERIAL PRIMARY KEY,
        settlement_id UUID NOT NULL REFERENCES oap_sika_market_settlement_intents(settlement_id)
            ON DELETE CASCADE,
        event_type TEXT NOT NULL,
        from_state TEXT,
        to_state TEXT,
        evidence JSONB NOT NULL DEFAULT '{}'::jsonb,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP)""",
    """CREATE INDEX IF NOT EXISTS ix_sika_market_settlement_order
       ON oap_sika_market_settlement_intents(order_id,created_at DESC)""",
)

MIGRATION_CHECKSUM = hashlib.sha256("\n".join(SCHEMA_STATEMENTS).encode()).hexdigest()


def _uuid(value: object, name: str) -> str:
    try:
        return str(UUID(str(value)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError(f"invalid_{name}") from exc


def _key(value: object) -> str:
    key = str(value or "").strip()
    if not _IDEMPOTENCY.fullmatch(key):
        raise ValueError("invalid_idempotency_key")
    return key


class SikaMarketSettlementStore:
    def create_for_order(
        self,
        *,
        order_id: object,
        actor_identity_id: object,
        idempotency_key: object,
        customer_approval_reference: object,
    ) -> dict[str, Any]:
        order = _uuid(order_id, "order_id")
        actor = _uuid(actor_identity_id, "actor_identity_id")
        key = _key(idempotency_key)
        customer_approval = str(customer_approval_reference or "").strip()
        if not customer_approval:
            raise ValueError("customer_approval_reference_required")

        payment_authority = market_execution_authority.STORE.status(
            capability="PAYMENT_CAPTURE"
        )
        transfer_authority = market_execution_authority.STORE.status(
            capability="MONEY_TRANSFER"
        )
        bank_ready = bool(
            payment_authority.get("authority_ready")
            and transfer_authority.get("authority_ready")
        )
        state = "READY_FOR_BANK" if bank_ready else "BANK_AUTHORITY_REQUIRED"
        bank_ref = (
            transfer_authority.get("provider_reference")
            if bank_ready
            else None
        )

        with postgres_db.connect() as connection:
            row = connection.execute(
                """SELECT o.buyer_identity_id,o.seller_identity_id,o.currency,o.subtotal_minor,
                          p.intent_id,p.amount_minor,p.currency
                   FROM oap_commerce_orders o
                   JOIN oap_commerce_payment_intents p ON p.order_id=o.order_id
                   WHERE o.order_id=%s FOR UPDATE""",
                (order,),
            ).fetchone()
            if row is None:
                raise ValueError("order_payment_intent_missing")
            if actor not in {str(row[0]), str(row[1])}:
                raise PermissionError("order_not_owned")
            if int(row[3]) != int(row[5]) or str(row[2]) != str(row[6]):
                raise RuntimeError("commerce_payment_amount_mismatch")

            existing = connection.execute(
                """SELECT settlement_id,state,bank_provider_reference,
                          customer_approval_reference,amount_minor,settlement_currency,
                          created_at,updated_at
                   FROM oap_sika_market_settlement_intents
                   WHERE buyer_identity_id=%s AND idempotency_key=%s""",
                (str(row[0]), key),
            ).fetchone()
            if existing is not None:
                return _view(existing, order_id=order, payment_intent_id=str(row[4]))

            created = connection.execute(
                """INSERT INTO oap_sika_market_settlement_intents(
                       order_id,payment_intent_id,buyer_identity_id,seller_identity_id,
                       amount_minor,settlement_currency,state,bank_provider_reference,
                       customer_approval_reference,idempotency_key)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                   RETURNING settlement_id,state,bank_provider_reference,
                             customer_approval_reference,amount_minor,
                             settlement_currency,created_at,updated_at""",
                (
                    order, str(row[4]), str(row[0]), str(row[1]),
                    int(row[5]), str(row[6]), state, bank_ref,
                    customer_approval, key,
                ),
            ).fetchone()
            connection.execute(
                """INSERT INTO oap_sika_market_settlement_events(
                       settlement_id,event_type,from_state,to_state,evidence)
                   VALUES (%s,'SIKA_SETTLEMENT_CREATED',NULL,%s,
                           jsonb_build_object(
                               'order_id',%s::text,
                               'payment_intent_id',%s::text,
                               'bank_authority_ready',%s,
                               'payment_execution_performed',false))""",
                (created[0], state, order, str(row[4]), bank_ready),
            )
            connection.commit()
        return _view(created, order_id=order, payment_intent_id=str(row[4]))

    def read_for_identity(
        self, *, settlement_id: object, identity_id: object
    ) -> dict[str, Any]:
        settlement = _uuid(settlement_id, "settlement_id")
        identity = _uuid(identity_id, "identity_id")
        with postgres_db.connect(readonly=True) as connection:
            row = connection.execute(
                """SELECT settlement_id,state,bank_provider_reference,
                          customer_approval_reference,amount_minor,settlement_currency,
                          created_at,updated_at,order_id,payment_intent_id
                   FROM oap_sika_market_settlement_intents
                   WHERE settlement_id=%s
                     AND (buyer_identity_id=%s OR seller_identity_id=%s)""",
                (settlement, identity, identity),
            ).fetchone()
            if row is None:
                raise PermissionError("settlement_not_owned")
        return _view(row[:8], order_id=str(row[8]), payment_intent_id=str(row[9]))


def _view(row: Any, *, order_id: str, payment_intent_id: str) -> dict[str, Any]:
    return {
        "settlement_id": str(row[0]),
        "order_id": order_id,
        "payment_intent_id": payment_intent_id,
        "route": "SIKA",
        "state": str(row[1]),
        "bank_provider_reference": str(row[2]) if row[2] else None,
        "customer_approval_reference": str(row[3]),
        "amount_minor": int(row[4]),
        "settlement_currency": str(row[5]),
        "created_at": row[6].isoformat(),
        "updated_at": row[7].isoformat(),
        "sika_issuance_performed": False,
        "ledger_posting_performed": False,
        "payment_capture_performed": False,
        "money_transfer_performed": False,
        "provider_execution_required": True,
        "human_authority_final": True,
    }


def migration_sql() -> str:
    statements = list(SCHEMA_STATEMENTS)
    statements.append(
        "INSERT INTO oap_schema_migrations(version,checksum) "
        f"VALUES ('{SIKA_MARKET_SETTLEMENT_MIGRATION_VERSION}','{MIGRATION_CHECKSUM}') "
        "ON CONFLICT (version) DO NOTHING"
    )
    return ";\n\n".join(statements) + ";\n"


STORE = SikaMarketSettlementStore()
