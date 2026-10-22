"""Durable OAP Eats merchant, menu and order state.

Persistence only. This module does not execute food service, payment settlement,
or courier dispatch. Those remain separately gated.
"""
from __future__ import annotations

import hashlib
import json
from contextlib import nullcontext
from decimal import Decimal
from typing import Any
from uuid import UUID

from . import postgres_db
from .oap_eats import PUBLIC_TRANSITION_ROLES, can_transition

MIGRATION_VERSION = "0001_oap_eats_core"
SCHEMA_STATEMENTS = (
    """CREATE TABLE IF NOT EXISTS oap_eats_merchants (
        merchant_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        owner_identity_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
        name TEXT NOT NULL CHECK (char_length(name) BETWEEN 1 AND 120),
        postcode TEXT,
        active BOOLEAN NOT NULL DEFAULT FALSE,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP)""",
    """CREATE INDEX IF NOT EXISTS ix_eats_merchants_owner
       ON oap_eats_merchants(owner_identity_id,created_at DESC)""",
    """CREATE TABLE IF NOT EXISTS oap_eats_menu_items (
        item_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        merchant_id UUID NOT NULL REFERENCES oap_eats_merchants(merchant_id) ON DELETE CASCADE,
        name TEXT NOT NULL CHECK (char_length(name) BETWEEN 1 AND 160),
        description TEXT NOT NULL DEFAULT '',
        amount_minor INTEGER NOT NULL CHECK (amount_minor >= 0),
        currency TEXT NOT NULL CHECK (char_length(currency)=3),
        available BOOLEAN NOT NULL DEFAULT TRUE,
        allergen_data JSONB NOT NULL DEFAULT '{}'::jsonb,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP)""",
    """CREATE INDEX IF NOT EXISTS ix_eats_menu_merchant
       ON oap_eats_menu_items(merchant_id,available,created_at)""",
    """CREATE TABLE IF NOT EXISTS oap_eats_orders (
        order_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        customer_identity_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
        merchant_id UUID NOT NULL REFERENCES oap_eats_merchants(merchant_id) ON DELETE RESTRICT,
        state TEXT NOT NULL DEFAULT 'created',
        items JSONB NOT NULL,
        amount_minor INTEGER NOT NULL CHECK (amount_minor >= 0),
        currency TEXT NOT NULL CHECK (char_length(currency)=3),
        fulfilment_mode TEXT NOT NULL CHECK (fulfilment_mode IN ('delivery','collection')),
        movement_booking_id UUID REFERENCES oap_movement_bookings(booking_id) ON DELETE SET NULL,
        payment_id TEXT,
        payment_hold_id TEXT,
        idempotency_key TEXT NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(customer_identity_id,idempotency_key))""",
    """CREATE INDEX IF NOT EXISTS ix_eats_orders_customer
       ON oap_eats_orders(customer_identity_id,created_at DESC)""",
    """CREATE INDEX IF NOT EXISTS ix_eats_orders_merchant
       ON oap_eats_orders(merchant_id,created_at DESC)""",
    """CREATE TABLE IF NOT EXISTS oap_eats_order_events (
        event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        order_id UUID NOT NULL REFERENCES oap_eats_orders(order_id) ON DELETE CASCADE,
        actor_identity_id UUID REFERENCES users(id) ON DELETE SET NULL,
        from_state TEXT,
        to_state TEXT NOT NULL,
        evidence JSONB NOT NULL DEFAULT '{}'::jsonb,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP)""",
)
MIGRATION_CHECKSUM = hashlib.sha256("\n".join(SCHEMA_STATEMENTS).encode()).hexdigest()


def _uuid(value: object, name: str) -> str:
    try:
        return str(UUID(str(value)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError(f"invalid_{name}") from exc


def _key(value: object) -> str:
    key = str(value or "").strip()
    if not 8 <= len(key) <= 160:
        raise ValueError("invalid_idempotency_key")
    if any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._:-" for c in key):
        raise ValueError("invalid_idempotency_key")
    return key


def init_schema(*, assume_yes: bool = False, dry_run: bool = False) -> dict[str, object]:
    if not assume_yes:
        raise RuntimeError("Explicit human approval required: pass --yes")
    if dry_run:
        return {"migration": MIGRATION_VERSION, "checksum": MIGRATION_CHECKSUM, "schema_ready": False, "dry_run": True, "human_authority_final": True}
    with postgres_db.connect() as connection:
        for statement in SCHEMA_STATEMENTS:
            connection.execute(statement)
        connection.commit()
    return {"migration": MIGRATION_VERSION, "checksum": MIGRATION_CHECKSUM, "schema_ready": True, "tables": 4, "human_authority_final": True}


class EatsStore:
    def create_order(self, *, customer_identity_id: object, merchant_id: object, items: object,
                     amount_minor: object, currency: object, fulfilment_mode: object,
                     idempotency_key: object) -> dict[str, Any]:
        customer = _uuid(customer_identity_id, "customer_identity_id")
        merchant = _uuid(merchant_id, "merchant_id")
        key = _key(idempotency_key)
        if not isinstance(items, list) or not items:
            raise ValueError("items_required")
        try:
            amount = int(amount_minor)
        except (TypeError, ValueError) as exc:
            raise ValueError("invalid_amount_minor") from exc
        if amount < 0:
            raise ValueError("invalid_amount_minor")
        curr = str(currency or "").upper().strip()
        if len(curr) != 3:
            raise ValueError("invalid_currency")
        mode = str(fulfilment_mode or "").lower().strip()
        if mode not in {"delivery", "collection"}:
            raise ValueError("invalid_fulfilment_mode")
        payload = json.dumps(items, separators=(",", ":"), sort_keys=True)
        with postgres_db.connect() as connection:
            active = connection.execute(
                "SELECT 1 FROM oap_eats_merchants WHERE merchant_id=%s AND active=TRUE",
                (merchant,),
            ).fetchone()
            if active is None:
                raise ValueError("merchant_unavailable")
            row = connection.execute(
                """INSERT INTO oap_eats_orders(
                       customer_identity_id,merchant_id,state,items,amount_minor,currency,
                       fulfilment_mode,idempotency_key)
                   VALUES (%s,%s,'created',%s::jsonb,%s,%s,%s,%s)
                   ON CONFLICT (customer_identity_id,idempotency_key) DO UPDATE
                   SET idempotency_key=EXCLUDED.idempotency_key
                   WHERE oap_eats_orders.merchant_id=EXCLUDED.merchant_id
                     AND oap_eats_orders.items IS NOT DISTINCT FROM EXCLUDED.items
                     AND oap_eats_orders.amount_minor=EXCLUDED.amount_minor
                     AND oap_eats_orders.currency=EXCLUDED.currency
                     AND oap_eats_orders.fulfilment_mode=EXCLUDED.fulfilment_mode
                   RETURNING order_id,merchant_id,state,amount_minor,currency,
                             fulfilment_mode,movement_booking_id,payment_id,payment_hold_id,
                             created_at,updated_at""",
                (customer, merchant, payload, amount, curr, mode, key),
            ).fetchone()
            if row is None:
                raise ValueError("idempotency_conflict")
            connection.execute(
                """INSERT INTO oap_eats_order_events(order_id,actor_identity_id,from_state,to_state,evidence)
                   VALUES (%s,%s,NULL,'created',%s::jsonb)""",
                (str(row[0]), customer, json.dumps({"idempotency_key": key})),
            )
            connection.commit()
        return _row(row)

    def transition(self, *, order_id: object, actor_identity_id: object, target_state: object) -> dict[str, Any]:
        order = _uuid(order_id, "order_id")
        actor = _uuid(actor_identity_id, "actor_identity_id")
        target = str(target_state or "").lower().strip()
        with postgres_db.connect() as connection:
            current = connection.execute(
                """SELECT o.state,o.customer_identity_id,m.owner_identity_id
                   FROM oap_eats_orders o JOIN oap_eats_merchants m ON m.merchant_id=o.merchant_id
                   WHERE o.order_id=%s FOR UPDATE""", (order,)
            ).fetchone()
            if current is None or actor not in {str(current[1]), str(current[2])}:
                raise PermissionError("order_not_owned")
            if not can_transition(str(current[0]), target):
                raise ValueError("order_transition_not_allowed")
            roles = set()
            if actor == str(current[1]):
                roles.add("customer")
            if actor == str(current[2]):
                roles.add("merchant")
            if not roles.intersection(PUBLIC_TRANSITION_ROLES.get(target, ())):
                raise PermissionError("order_transition_role_denied")
            row = connection.execute(
                """UPDATE oap_eats_orders SET state=%s,updated_at=CURRENT_TIMESTAMP
                   WHERE order_id=%s
                   RETURNING order_id,merchant_id,state,amount_minor,currency,
                             fulfilment_mode,movement_booking_id,payment_id,payment_hold_id,
                             created_at,updated_at""", (target, order)
            ).fetchone()
            connection.execute(
                """INSERT INTO oap_eats_order_events(order_id,actor_identity_id,from_state,to_state)
                   VALUES (%s,%s,%s,%s)""", (order, actor, str(current[0]), target)
            )
            connection.commit()
        return _row(row)

    def read_order(self, *, order_id: object, identity_id: object) -> dict[str, Any]:
        order = _uuid(order_id, "order_id")
        identity = _uuid(identity_id, "identity_id")
        with postgres_db.connect(readonly=True) as connection:
            row = connection.execute(
                """SELECT o.order_id,o.merchant_id,o.state,o.amount_minor,o.currency,
                          o.fulfilment_mode,o.movement_booking_id,o.payment_id,o.payment_hold_id,
                          o.created_at,o.updated_at
                   FROM oap_eats_orders o
                   JOIN oap_eats_merchants m ON m.merchant_id=o.merchant_id
                   WHERE o.order_id=%s
                     AND (o.customer_identity_id=%s OR m.owner_identity_id=%s)""",
                (order, identity, identity),
            ).fetchone()
        if row is None:
            raise PermissionError("order_not_owned")
        return _row(row)

    def bind_payment(self, *, order_id: object, customer_identity_id: object, payment_id: object,
                     hold_id: object, payer_account_id: object) -> dict[str, Any]:
        """Bind canonical SIKA evidence atomically; never execute a payment.

        Preflight reads are advisory. Lock order is Eats order, payer account,
        intent, then hold, consistent with SIKA's account-first creation and
        intent-before-hold lifecycle updates. Serializing on the intent makes
        the subsequent cross-order lookup see a competing binder's commit.
        """
        order = _uuid(order_id, "order_id")
        customer = _uuid(customer_identity_id, "customer_identity_id")
        payment = str(payment_id or "").strip()
        hold = str(hold_id or "").strip()
        payer = str(payer_account_id or "").strip()
        if not payment or not hold or not payer:
            raise ValueError("payment_binding_required")
        with postgres_db.connect() as connection:
            # The lookup after waiting for the intent lock must see the prior
            # binder's commit, even if the database default is repeatable read.
            connection.execute("SET TRANSACTION ISOLATION LEVEL READ COMMITTED")
            owned = self.require_customer_order(
                order_id=order, customer_identity_id=customer, connection=connection,
            )
            account = connection.execute(
                """SELECT owner_reference,status,currency FROM oap_sika_accounts
                   WHERE account_id=%s FOR SHARE""", (payer,),
            ).fetchone()
            if account is None or str(account[0]) != customer or str(account[1]) != "OPEN":
                raise PermissionError("order_payment_binding_denied")
            intent = connection.execute(
                """SELECT payer_account_id,amount,currency,status
                   FROM oap_sika_payment_intents WHERE payment_id=%s FOR UPDATE""",
                (payment,),
            ).fetchone()
            if intent is None:
                raise ValueError("payment_intent_not_found")
            if str(intent[0]) != payer:
                raise ValueError("payment_payer_binding_changed")
            if str(intent[3]) not in {"AUTHORISED", "SUBMITTED"}:
                raise ValueError("payment_intent_not_bindable")
            reservation = connection.execute(
                """SELECT hold_id,payer_account_id,amount,currency,status
                   FROM oap_sika_payment_holds WHERE payment_id=%s FOR UPDATE""",
                (payment,),
            ).fetchone()
            if reservation is None or str(reservation[4]) != "ACTIVE":
                raise ValueError("active_payment_hold_required")
            if str(reservation[0]) != hold or str(reservation[1]) != payer:
                raise ValueError("payment_hold_binding_mismatch")
            expected = Decimal(owned["amount_minor"]) / Decimal(100)
            if Decimal(intent[1]) != expected or Decimal(reservation[2]) != expected:
                raise ValueError("payment_amount_mismatch")
            if any(str(currency) != owned["currency"] for currency in (account[2], intent[2], reservation[3])):
                raise ValueError("payment_currency_mismatch")
            reused = connection.execute(
                """SELECT 1 FROM oap_eats_orders
                   WHERE order_id<>%s AND (payment_id=%s OR payment_hold_id=%s)
                   LIMIT 1""", (order, payment, hold),
            ).fetchone()
            if reused is not None:
                raise PermissionError("payment_already_bound_to_order")
            if owned["payment_id"] == payment and owned["payment_hold_id"] == hold:
                # A lost-response retry is a read of the existing binding,
                # without another event or a changed timestamp.
                connection.commit()
                return {**owned, "payment_status": str(intent[3]), "hold_status": str(reservation[4])}
            row = connection.execute(
                """UPDATE oap_eats_orders
                   SET payment_id=%s,payment_hold_id=%s,updated_at=CURRENT_TIMESTAMP
                   WHERE order_id=%s AND customer_identity_id=%s
                     AND (payment_id IS NULL OR payment_id=%s)
                     AND (payment_hold_id IS NULL OR payment_hold_id=%s)
                   RETURNING order_id,merchant_id,state,amount_minor,currency,
                             fulfilment_mode,movement_booking_id,payment_id,payment_hold_id,
                             created_at,updated_at""",
                (payment, hold, order, customer, payment, hold),
            ).fetchone()
            if row is None:
                raise PermissionError("order_payment_binding_denied")
            connection.execute(
                """INSERT INTO oap_eats_order_events(order_id,actor_identity_id,from_state,to_state,evidence)
                   VALUES (%s,%s,%s,%s,%s::jsonb)""",
                (order, customer, str(row[2]), str(row[2]), json.dumps({"payment_id": payment, "hold_id": hold})),
            )
            connection.commit()
        return {**_row(row), "payment_status": str(intent[3]), "hold_status": str(reservation[4])}

    def require_customer_order(self, *, order_id: object, customer_identity_id: object,
                               connection: Any = None) -> dict[str, Any]:
        """Fail closed unless the caller owns the order as its customer.

        Merchant read permission is intentionally insufficient for delivery booking.
        """
        order = _uuid(order_id, "order_id")
        customer = _uuid(customer_identity_id, "customer_identity_id")
        with (nullcontext(connection) if connection is not None else postgres_db.connect(readonly=True)) as db:
            row = db.execute(
                """SELECT order_id,merchant_id,state,amount_minor,currency,
                          fulfilment_mode,movement_booking_id,payment_id,payment_hold_id,
                          created_at,updated_at
                   FROM oap_eats_orders
                   WHERE order_id=%s AND customer_identity_id=%s"""
                + (" FOR UPDATE" if connection is not None else ""),
                (order, customer),
            ).fetchone()
        if row is None:
            raise PermissionError("order_customer_required")
        return _row(row)

    def bind_movement(self, *, order_id: object, customer_identity_id: object, booking_id: object,
                      connection: Any = None) -> dict[str, Any]:
        order = _uuid(order_id, "order_id")
        customer = _uuid(customer_identity_id, "customer_identity_id")
        booking = _uuid(booking_id, "booking_id")
        with (nullcontext(connection) if connection is not None else postgres_db.connect()) as db:
            row = db.execute(
                """UPDATE oap_eats_orders
                   SET movement_booking_id=%s,updated_at=CURRENT_TIMESTAMP
                   WHERE order_id=%s AND customer_identity_id=%s
                     AND fulfilment_mode='delivery'
                     AND (movement_booking_id IS NULL OR movement_booking_id=%s)
                   RETURNING order_id,merchant_id,state,amount_minor,currency,
                             fulfilment_mode,movement_booking_id,payment_id,payment_hold_id,
                             created_at,updated_at""",
                (booking, order, customer, booking),
            ).fetchone()
            if row is None:
                raise PermissionError("order_movement_binding_denied")
            db.execute(
                """INSERT INTO oap_eats_order_events(order_id,actor_identity_id,from_state,to_state,evidence)
                   VALUES (%s,%s,%s,%s,%s::jsonb)""",
                (order, customer, str(row[2]), str(row[2]), json.dumps({"movement_booking_id": booking})),
            )
            if connection is None:
                db.commit()
        return _row(row)


def _row(row) -> dict[str, Any]:
    return {
        "order_id": str(row[0]), "merchant_id": str(row[1]), "state": str(row[2]),
        "amount_minor": int(row[3]), "currency": str(row[4]), "fulfilment_mode": str(row[5]),
        "movement_booking_id": str(row[6]) if row[6] else None,
        "payment_id": str(row[7]) if row[7] else None,
        "payment_hold_id": str(row[8]) if row[8] else None,
        "created_at": row[9].isoformat() if hasattr(row[9], "isoformat") else str(row[9]),
        "updated_at": row[10].isoformat() if hasattr(row[10], "isoformat") else str(row[10]),
        "payment_captured": False, "courier_dispatched": False,
    }


STORE = EatsStore()
