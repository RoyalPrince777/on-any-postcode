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

# A separate, recorded migration preserves the original schema checksum. NULL
# deliberately leaves historical client-priced orders unverified.
PRICING_VERSION = "eats_catalogue_v1"
INTEGRITY_MIGRATION_VERSION = "0002_oap_eats_order_integrity"
INTEGRITY_SCHEMA_STATEMENTS = (
    "ALTER TABLE oap_eats_orders ADD COLUMN IF NOT EXISTS pricing_version TEXT",
)
INTEGRITY_MIGRATION_CHECKSUM = hashlib.sha256("\n".join(INTEGRITY_SCHEMA_STATEMENTS).encode()).hexdigest()


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


def _basket(items: object) -> list[dict[str, Any]]:
    if not isinstance(items, list) or not 1 <= len(items) <= 100:
        raise ValueError("items_required")
    basket = {}
    for item in items:
        if not isinstance(item, dict) or set(item) != {"item_id", "quantity"}:
            raise ValueError("invalid_order_item")
        item_id = _uuid(item["item_id"], "item_id")
        quantity = item["quantity"]
        if type(quantity) is not int or not 1 <= quantity <= 99:
            raise ValueError("invalid_item_quantity")
        if item_id in basket:
            raise ValueError("duplicate_order_item")
        basket[item_id] = quantity
    return [{"item_id": item_id, "quantity": basket[item_id]} for item_id in sorted(basket)]


def init_schema(*, assume_yes: bool = False, dry_run: bool = False) -> dict[str, object]:
    if not assume_yes:
        raise RuntimeError("Explicit human approval required: pass --yes")
    if dry_run:
        return {"migration": MIGRATION_VERSION, "checksum": MIGRATION_CHECKSUM,
                "integrity_migration": INTEGRITY_MIGRATION_VERSION,
                "integrity_checksum": INTEGRITY_MIGRATION_CHECKSUM,
                "schema_ready": False, "dry_run": True, "human_authority_final": True}
    with postgres_db.connect() as connection:
        connection.execute("SET TRANSACTION ISOLATION LEVEL READ COMMITTED")
        connection.execute("SELECT pg_advisory_xact_lock(%s)", (25820002,))
        for statement in SCHEMA_STATEMENTS:
            connection.execute(statement)
        applied = connection.execute(
            "SELECT checksum FROM oap_schema_migrations WHERE version=%s",
            (INTEGRITY_MIGRATION_VERSION,),
        ).fetchone()
        if applied is not None and str(applied[0]) != INTEGRITY_MIGRATION_CHECKSUM:
            raise RuntimeError("Eats integrity migration checksum mismatch")
        if applied is None:
            for statement in INTEGRITY_SCHEMA_STATEMENTS:
                connection.execute(statement)
            connection.execute(
                "INSERT INTO oap_schema_migrations(version,checksum) VALUES (%s,%s)",
                (INTEGRITY_MIGRATION_VERSION, INTEGRITY_MIGRATION_CHECKSUM),
            )
        column = connection.execute(
            """SELECT format_type(atttypid,atttypmod) FROM pg_attribute
               WHERE attrelid='oap_eats_orders'::regclass AND attname='pricing_version'
                 AND NOT attisdropped""",
        ).fetchone()
        if column is None or str(column[0]) != "text":
            raise RuntimeError("Eats integrity schema mismatch")
        connection.commit()
    return {"migration": MIGRATION_VERSION, "checksum": MIGRATION_CHECKSUM,
            "integrity_migration": INTEGRITY_MIGRATION_VERSION,
            "integrity_checksum": INTEGRITY_MIGRATION_CHECKSUM,
            "schema_ready": True, "tables": 4, "human_authority_final": True}


class EatsStore:
    def create_order(self, *, customer_identity_id: object, merchant_id: object, items: object,
                     amount_minor: object, currency: object, fulfilment_mode: object,
                     idempotency_key: object) -> dict[str, Any]:
        customer = _uuid(customer_identity_id, "customer_identity_id")
        merchant = _uuid(merchant_id, "merchant_id")
        key = _key(idempotency_key)
        basket = _basket(items)
        # A supplied total is only a quote assertion. It cannot set the price.
        if amount_minor is not None and (type(amount_minor) is not int or amount_minor < 0):
            raise ValueError("invalid_amount_minor")
        curr = str(currency or "").upper().strip()
        if len(curr) != 3 or not curr.isascii() or not curr.isalpha():
            raise ValueError("invalid_currency")
        mode = str(fulfilment_mode or "").lower().strip()
        if mode not in {"delivery", "collection"}:
            raise ValueError("invalid_fulfilment_mode")
        with postgres_db.connect() as connection:
            connection.execute("SET TRANSACTION ISOLATION LEVEL READ COMMITTED")
            lock = int.from_bytes(hashlib.sha256(f"eats-order:{customer}:{key}".encode()).digest()[:8], signed=True)
            connection.execute("SELECT pg_advisory_xact_lock(%s)", (lock,))
            existing = connection.execute(
                """SELECT order_id,merchant_id,state,amount_minor,currency,
                          fulfilment_mode,movement_booking_id,payment_id,payment_hold_id,
                          created_at,updated_at,items,pricing_version
                   FROM oap_eats_orders WHERE customer_identity_id=%s AND idempotency_key=%s
                   FOR UPDATE""", (customer, key),
            ).fetchone()
            if existing is not None:
                if existing[12] != PRICING_VERSION:
                    raise ValueError("legacy_order_reprice_required")
                original_basket = [{"item_id": item["item_id"], "quantity": item["quantity"]} for item in existing[11]]
                if (str(existing[1]) != merchant or original_basket != basket
                        or str(existing[4]) != curr or str(existing[5]) != mode
                        or (amount_minor is not None and amount_minor != int(existing[3]))):
                    raise ValueError("idempotency_conflict")
                connection.commit()
                return _row(existing)
            active = connection.execute(
                "SELECT 1 FROM oap_eats_merchants WHERE merchant_id=%s AND active=TRUE FOR SHARE",
                (merchant,),
            ).fetchone()
            if active is None:
                raise ValueError("merchant_unavailable")
            menu = connection.execute(
                """SELECT item_id,merchant_id,name,amount_minor,currency,available
                   FROM oap_eats_menu_items WHERE item_id=ANY(%s::uuid[])
                   ORDER BY item_id FOR SHARE""", ([item["item_id"] for item in basket],),
            ).fetchall()
            if (len(menu) != len(basket)
                    or any(str(item[1]) != merchant or item[5] is not True for item in menu)):
                raise ValueError("menu_item_unavailable")
            if any(str(item[4]) != curr for item in menu):
                raise ValueError("menu_currency_mismatch")
            snapshot = [{**requested, "name": str(item[2]), "unit_amount_minor": int(item[3]),
                         "currency": str(item[4])} for requested, item in zip(basket, menu, strict=True)]
            amount = sum(item["quantity"] * item["unit_amount_minor"] for item in snapshot)
            if amount > 2_147_483_647:
                raise ValueError("order_total_out_of_range")
            if amount_minor is not None and amount_minor != amount:
                raise ValueError("order_total_mismatch")
            payload = json.dumps(snapshot, separators=(",", ":"), sort_keys=True)
            row = connection.execute(
                """INSERT INTO oap_eats_orders(
                       customer_identity_id,merchant_id,state,items,amount_minor,currency,
                       fulfilment_mode,idempotency_key,pricing_version)
                   VALUES (%s,%s,'created',%s::jsonb,%s,%s,%s,%s,%s)
                   RETURNING order_id,merchant_id,state,amount_minor,currency,
                             fulfilment_mode,movement_booking_id,payment_id,payment_hold_id,
                             created_at,updated_at""",
                (customer, merchant, payload, amount, curr, mode, key, PRICING_VERSION),
            ).fetchone()
            connection.execute(
                """INSERT INTO oap_eats_order_events(order_id,actor_identity_id,from_state,to_state,evidence)
                   VALUES (%s,%s,NULL,'created',%s::jsonb)""",
                (str(row[0]), customer, json.dumps({"idempotency_key": key, "pricing_version": PRICING_VERSION,
                                                   "amount_minor": amount, "currency": curr})),
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

        Eats defines payee_reference as a SIKA account ID owned by the current
        merchant owner. An arbitrary merchant label is insufficient.
        Preflight reads are advisory. Lock order is Eats order, merchant,
        accounts in ID order, intent, then hold, consistent with account-first creation and
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
            pricing = connection.execute(
                "SELECT pricing_version FROM oap_eats_orders WHERE order_id=%s", (order,),
            ).fetchone()
            if pricing is None or pricing[0] != PRICING_VERSION:
                raise ValueError("legacy_order_reprice_required")
            merchant = connection.execute(
                """SELECT owner_identity_id,active FROM oap_eats_merchants
                   WHERE merchant_id=%s FOR SHARE""", (owned["merchant_id"],),
            ).fetchone()
            if merchant is None or merchant[1] is not True:
                raise ValueError("merchant_unavailable")
            # Only a hint for account lock ordering; the locked intent below
            # must still name exactly this account before any binding write.
            payee_hint = connection.execute(
                "SELECT payee_reference FROM oap_sika_payment_intents WHERE payment_id=%s", (payment,),
            ).fetchone()
            if payee_hint is None:
                raise ValueError("payment_intent_not_found")
            payee = str(payee_hint[0])
            accounts = {str(row[0]): row for row in connection.execute(
                """SELECT account_id,owner_reference,status,currency FROM oap_sika_accounts
                   WHERE account_id=ANY(%s) ORDER BY account_id FOR SHARE""", ([payer, payee],),
            ).fetchall()}
            account = accounts.get(payer)
            recipient = accounts.get(payee)
            if account is None or str(account[1]) != customer or str(account[2]) != "OPEN":
                raise PermissionError("order_payment_binding_denied")
            if recipient is None or str(recipient[1]) != str(merchant[0]) or str(recipient[2]) != "OPEN":
                raise PermissionError("payment_payee_not_owned_by_merchant_or_open")
            intent = connection.execute(
                """SELECT payer_account_id,amount,currency,status,payee_reference
                   FROM oap_sika_payment_intents WHERE payment_id=%s FOR UPDATE""",
                (payment,),
            ).fetchone()
            if intent is None:
                raise ValueError("payment_intent_not_found")
            if str(intent[0]) != payer:
                raise ValueError("payment_payer_binding_changed")
            if str(intent[4]) != payee:
                raise ValueError("payment_payee_binding_changed")
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
            if any(str(currency) != owned["currency"] for currency in (account[3], recipient[3], intent[2], reservation[3])):
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
                (order, customer, str(row[2]), str(row[2]), json.dumps({
                    "payment_id": payment, "hold_id": hold, "payee_account_id": payee,
                    "merchant_id": owned["merchant_id"], "pricing_version": PRICING_VERSION,
                })),
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
