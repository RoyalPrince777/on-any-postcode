"""OAP Market transaction correlation spine.

This module connects existing first-party Commerce, Movement and Post records
without replacing their ownership. It records references and recovery state only.

Truth boundaries:
- no payment capture or money transfer
- no external fulfilment or carrier handoff
- no automatic dispatch
- STOP blocks consequential progression
- recovery preserves evidence and never rewrites authority
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from . import postgres_db

MARKET_TRANSACTION_MIGRATION_VERSION = "0007_market_transaction_spine"

TRANSACTION_STATES = frozenset({
    "OPEN",
    "ORDER_RECORDED",
    "FULFILMENT_PENDING",
    "MOVEMENT_PENDING",
    "PARCEL_PENDING",
    "READY",
    "COMPLETED",
    "STOPPED",
    "RECOVERY_REQUIRED",
    "FAILED",
    "CANCELLED",
})
STOP_STATES = frozenset({"NONE", "REQUESTED", "STOPPED", "RECOVERY_REQUIRED", "CLEARED_BY_HUMAN"})
RECOVERY_STATES = frozenset({"NONE", "REQUIRED", "IN_PROGRESS", "RECOVERED", "FAILED"})

MARKET_TRANSACTION_SCHEMA_STATEMENTS = (
    """CREATE TABLE IF NOT EXISTS oap_market_transactions (
        transaction_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        buyer_identity_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
        seller_identity_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
        order_id UUID NOT NULL UNIQUE
            REFERENCES oap_commerce_orders(order_id) ON DELETE RESTRICT,
        fulfilment_intent_id UUID UNIQUE
            REFERENCES oap_commerce_fulfilment_intents(fulfilment_id)
            ON DELETE SET NULL,
        movement_booking_id UUID UNIQUE
            REFERENCES oap_movement_bookings(booking_id) ON DELETE SET NULL,
        parcel_id UUID UNIQUE
            REFERENCES oap_post_office_parcels(parcel_id) ON DELETE SET NULL,
        settlement_intent_id UUID
            REFERENCES oap_commerce_payment_intents(intent_id) ON DELETE SET NULL,
        state TEXT NOT NULL DEFAULT 'ORDER_RECORDED'
            CHECK (state IN (
                'OPEN','ORDER_RECORDED','FULFILMENT_PENDING','MOVEMENT_PENDING',
                'PARCEL_PENDING','READY','COMPLETED','STOPPED',
                'RECOVERY_REQUIRED','FAILED','CANCELLED')),
        stop_state TEXT NOT NULL DEFAULT 'NONE'
            CHECK (stop_state IN (
                'NONE','REQUESTED','STOPPED','RECOVERY_REQUIRED','CLEARED_BY_HUMAN')),
        recovery_state TEXT NOT NULL DEFAULT 'NONE'
            CHECK (recovery_state IN (
                'NONE','REQUIRED','IN_PROGRESS','RECOVERED','FAILED')),
        idempotency_key TEXT NOT NULL,
        last_good_stage TEXT NOT NULL DEFAULT 'ORDER_RECORDED',
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(buyer_identity_id,idempotency_key))""",
    """CREATE INDEX IF NOT EXISTS ix_market_transaction_buyer_created
        ON oap_market_transactions(buyer_identity_id, created_at DESC)""",
    """CREATE INDEX IF NOT EXISTS ix_market_transaction_seller_created
        ON oap_market_transactions(seller_identity_id, created_at DESC)""",
    """CREATE TABLE IF NOT EXISTS oap_market_transaction_events (
        event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        transaction_id UUID NOT NULL
            REFERENCES oap_market_transactions(transaction_id) ON DELETE CASCADE,
        actor_identity_id UUID REFERENCES users(id) ON DELETE SET NULL,
        event_type TEXT NOT NULL,
        from_state TEXT,
        to_state TEXT,
        evidence JSONB NOT NULL DEFAULT '{}'::jsonb,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP)""",
    """CREATE INDEX IF NOT EXISTS ix_market_transaction_event_created
        ON oap_market_transaction_events(transaction_id, created_at ASC)""",
)

MARKET_TRANSACTION_MIGRATION_CHECKSUM = hashlib.sha256(
    "\n".join(MARKET_TRANSACTION_SCHEMA_STATEMENTS).encode()
).hexdigest()


@dataclass(frozen=True)
class CorrelationRefs:
    order_id: str
    fulfilment_intent_id: str | None = None
    movement_booking_id: str | None = None
    parcel_id: str | None = None
    settlement_intent_id: str | None = None


def _uuid(value: object, name: str) -> str:
    try:
        return str(UUID(str(value)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError(f"invalid_{name}") from exc


def _idempotency(value: object) -> str:
    key = str(value or "").strip()
    if not 8 <= len(key) <= 160:
        raise ValueError("invalid_idempotency_key")
    allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._:-")
    if any(char not in allowed for char in key):
        raise ValueError("invalid_idempotency_key")
    return key


def derive_recovery_state(
    *,
    order_present: bool,
    fulfilment_expected: bool,
    fulfilment_present: bool,
    movement_expected: bool,
    movement_present: bool,
    parcel_expected: bool,
    parcel_present: bool,
    stopped: bool = False,
) -> dict[str, str]:
    """Return the smallest truthful durable state without inventing completion."""
    if not order_present:
        return {
            "state": "RECOVERY_REQUIRED",
            "recovery_state": "REQUIRED",
            "last_good_stage": "OPEN",
            "reason": "order_missing",
        }
    if stopped:
        return {
            "state": "STOPPED",
            "recovery_state": "NONE",
            "last_good_stage": "ORDER_RECORDED",
            "reason": "stop_active",
        }
    if fulfilment_expected and not fulfilment_present:
        return {
            "state": "RECOVERY_REQUIRED",
            "recovery_state": "REQUIRED",
            "last_good_stage": "ORDER_RECORDED",
            "reason": "fulfilment_intent_missing",
        }
    if movement_expected and not movement_present:
        return {
            "state": "RECOVERY_REQUIRED",
            "recovery_state": "REQUIRED",
            "last_good_stage": "FULFILMENT_PENDING",
            "reason": "movement_booking_missing",
        }
    if parcel_expected and not parcel_present:
        return {
            "state": "RECOVERY_REQUIRED",
            "recovery_state": "REQUIRED",
            "last_good_stage": "MOVEMENT_PENDING",
            "reason": "parcel_missing",
        }
    if parcel_present:
        return {
            "state": "READY",
            "recovery_state": "NONE",
            "last_good_stage": "PARCEL_PENDING",
            "reason": "references_consistent",
        }
    if movement_present:
        return {
            "state": "PARCEL_PENDING",
            "recovery_state": "NONE",
            "last_good_stage": "MOVEMENT_PENDING",
            "reason": "awaiting_parcel",
        }
    if fulfilment_present:
        return {
            "state": "MOVEMENT_PENDING",
            "recovery_state": "NONE",
            "last_good_stage": "FULFILMENT_PENDING",
            "reason": "awaiting_movement",
        }
    return {
        "state": "FULFILMENT_PENDING",
        "recovery_state": "NONE",
        "last_good_stage": "ORDER_RECORDED",
        "reason": "awaiting_fulfilment",
    }


def consequential_action_allowed(*, stop_state: str, recovery_state: str) -> bool:
    """Fail closed for STOP and unresolved recovery."""
    if stop_state not in STOP_STATES or recovery_state not in RECOVERY_STATES:
        return False
    if stop_state in {"REQUESTED", "STOPPED", "RECOVERY_REQUIRED"}:
        return False
    return recovery_state not in {"REQUIRED", "IN_PROGRESS", "FAILED"}


class MarketTransactionStore:
    """Durable correlation only; authoritative state remains in source organs."""

    def create_from_order(
        self,
        *,
        buyer_identity_id: object,
        order_id: object,
        idempotency_key: object,
    ) -> dict[str, Any]:
        buyer = _uuid(buyer_identity_id, "buyer_identity_id")
        order = _uuid(order_id, "order_id")
        key = _idempotency(idempotency_key)
        with postgres_db.connect() as connection:
            owned = connection.execute(
                """SELECT buyer_identity_id,seller_identity_id
                   FROM oap_commerce_orders
                   WHERE order_id=%s AND buyer_identity_id=%s
                   FOR UPDATE""",
                (order, buyer),
            ).fetchone()
            if owned is None:
                raise PermissionError("order_not_owned")
            seller = str(owned[1])
            row = connection.execute(
                """INSERT INTO oap_market_transactions(
                       buyer_identity_id,seller_identity_id,order_id,
                       state,stop_state,recovery_state,idempotency_key,last_good_stage)
                   VALUES (%s,%s,%s,'ORDER_RECORDED','NONE','NONE',%s,'ORDER_RECORDED')
                   ON CONFLICT (buyer_identity_id,idempotency_key) DO UPDATE
                   SET idempotency_key=EXCLUDED.idempotency_key
                   WHERE oap_market_transactions.order_id=EXCLUDED.order_id
                   RETURNING transaction_id,order_id,state,stop_state,
                             recovery_state,last_good_stage,created_at,updated_at""",
                (buyer, seller, order, key),
            ).fetchone()
            if row is None:
                raise ValueError("idempotency_conflict")
            self._event(
                connection,
                transaction_id=str(row[0]),
                actor_identity_id=buyer,
                event_type="TRANSACTION_CREATED",
                from_state=None,
                to_state=str(row[2]),
                evidence={"order_id": order},
            )
            connection.commit()
        return _row(row)

    def read_for_identity(
        self, *, transaction_id: object, identity_id: object
    ) -> dict[str, Any]:
        transaction = _uuid(transaction_id, "transaction_id")
        identity = _uuid(identity_id, "identity_id")
        with postgres_db.connect(readonly=True) as connection:
            row = connection.execute(
                """SELECT transaction_id,order_id,state,stop_state,recovery_state,
                          last_good_stage,created_at,updated_at,
                          fulfilment_intent_id,movement_booking_id,parcel_id,
                          settlement_intent_id
                   FROM oap_market_transactions
                   WHERE transaction_id=%s
                     AND (buyer_identity_id=%s OR seller_identity_id=%s)""",
                (transaction, identity, identity),
            ).fetchone()
        if row is None:
            raise PermissionError("transaction_not_owned")
        result = _row(row[:8])
        result["refs"] = {
            "fulfilment_intent_id": str(row[8]) if row[8] else None,
            "movement_booking_id": str(row[9]) if row[9] else None,
            "parcel_id": str(row[10]) if row[10] else None,
            "settlement_intent_id": str(row[11]) if row[11] else None,
        }
        result["payment_capture_performed"] = False
        result["external_fulfilment_performed"] = False
        result["carrier_handoff_performed"] = False
        return result

    def stop(
        self, *, transaction_id: object, actor_identity_id: object
    ) -> dict[str, Any]:
        transaction = _uuid(transaction_id, "transaction_id")
        actor = _uuid(actor_identity_id, "actor_identity_id")
        with postgres_db.connect() as connection:
            current = connection.execute(
                """SELECT state,buyer_identity_id,seller_identity_id
                   FROM oap_market_transactions
                   WHERE transaction_id=%s FOR UPDATE""",
                (transaction,),
            ).fetchone()
            if current is None or actor not in {str(current[1]), str(current[2])}:
                raise PermissionError("transaction_not_owned")
            row = connection.execute(
                """UPDATE oap_market_transactions
                   SET state='STOPPED',stop_state='STOPPED',
                       updated_at=CURRENT_TIMESTAMP
                   WHERE transaction_id=%s
                   RETURNING transaction_id,order_id,state,stop_state,
                             recovery_state,last_good_stage,created_at,updated_at""",
                (transaction,),
            ).fetchone()
            self._event(
                connection,
                transaction_id=transaction,
                actor_identity_id=actor,
                event_type="STOP",
                from_state=str(current[0]),
                to_state="STOPPED",
                evidence={"consequential_action_allowed": False},
            )
            connection.commit()
        return _row(row)

    @staticmethod
    def _event(
        connection: Any,
        *,
        transaction_id: str,
        actor_identity_id: str | None,
        event_type: str,
        from_state: str | None,
        to_state: str | None,
        evidence: dict[str, Any],
    ) -> None:
        connection.execute(
            """INSERT INTO oap_market_transaction_events(
                   transaction_id,actor_identity_id,event_type,
                   from_state,to_state,evidence)
               VALUES (%s,%s,%s,%s,%s,%s::jsonb)""",
            (
                transaction_id,
                actor_identity_id,
                event_type,
                from_state,
                to_state,
                json.dumps(evidence, sort_keys=True),
            ),
        )


def _row(row: Any) -> dict[str, Any]:
    return {
        "transaction_id": str(row[0]),
        "order_id": str(row[1]),
        "state": str(row[2]),
        "stop_state": str(row[3]),
        "recovery_state": str(row[4]),
        "last_good_stage": str(row[5]),
        "created_at": row[6].isoformat(),
        "updated_at": row[7].isoformat(),
        "payment_capture_performed": False,
        "external_fulfilment_performed": False,
        "carrier_handoff_performed": False,
        "human_authority_final": True,
    }


def migration_sql() -> str:
    statements = list(MARKET_TRANSACTION_SCHEMA_STATEMENTS)
    statements.append(
        "INSERT INTO oap_schema_migrations(version,checksum) "
        f"VALUES ('{MARKET_TRANSACTION_MIGRATION_VERSION}',"
        f"'{MARKET_TRANSACTION_MIGRATION_CHECKSUM}') "
        "ON CONFLICT (version) DO NOTHING"
    )
    return ";\n\n".join(statements) + ";\n"


def platform_status() -> dict[str, object]:
    """Report transaction-spine truth boundaries without claiming live DB proof."""
    return {
        "component": "OAP Market Transaction Spine",
        "correlation_authored": True,
        "payment_capture_performed": False,
        "money_transfer_performed": False,
        "external_fulfilment_performed": False,
        "carrier_handoff_performed": False,
        "automatic_dispatch_performed": False,
        "live_database_migration_proven": False,
        "live_runtime_readback_proven": False,
        "human_authority_final": True,
    }


STORE = MarketTransactionStore()
