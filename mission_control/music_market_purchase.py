"""First-party OAP Music × Market purchase correlation spine.

This module links an existing OAP Music release to an existing OAP Market product,
then converts an already-captured Commerce payment into a durable Music ownership
entitlement and deterministic split ledger.

Truth boundaries:
- never captures payment or moves money
- never invents rights; READY requires an owned Music evidence receipt
- ownership is granted only after Commerce reports CAPTURED
- payouts remain provider-required until a separate lawful payout rail exists
- idempotent order/entitlement creation and immutable commercial facts
"""
from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping
from typing import Any
from uuid import UUID, uuid4

from . import postgres_db

MIGRATION_VERSION = "0014_music_market_purchase_spine"

SCHEMA_STATEMENTS = (
    """CREATE TABLE IF NOT EXISTS oap_music_market_products (
        music_market_product_id UUID PRIMARY KEY,
        seller_identity_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
        release_id UUID NOT NULL UNIQUE
            REFERENCES oap_music_releases(release_id) ON DELETE RESTRICT,
        product_id UUID NOT NULL UNIQUE REFERENCES products(id) ON DELETE RESTRICT,
        rights_evidence_receipt_id UUID NOT NULL
            REFERENCES oap_music_evidence_receipts(receipt_id) ON DELETE RESTRICT,
        minimum_price_minor BIGINT NOT NULL DEFAULT 100
            CHECK (minimum_price_minor >= 100),
        optional_pay_more BOOLEAN NOT NULL DEFAULT TRUE,
        split_plan JSONB NOT NULL,
        state TEXT NOT NULL DEFAULT 'READY'
            CHECK (state IN ('READY','STOPPED','RECOVERY_REQUIRED')),
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE TABLE IF NOT EXISTS oap_music_purchase_entitlements (
        entitlement_id UUID PRIMARY KEY,
        buyer_identity_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
        seller_identity_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
        music_market_product_id UUID NOT NULL
            REFERENCES oap_music_market_products(music_market_product_id)
            ON DELETE RESTRICT,
        release_id UUID NOT NULL REFERENCES oap_music_releases(release_id)
            ON DELETE RESTRICT,
        order_id UUID NOT NULL UNIQUE REFERENCES oap_commerce_orders(order_id)
            ON DELETE RESTRICT,
        amount_minor BIGINT NOT NULL CHECK (amount_minor >= 100),
        currency TEXT NOT NULL CHECK (currency='GBP'),
        state TEXT NOT NULL DEFAULT 'OWNED'
            CHECK (state IN ('OWNED','REFUNDED','DISPUTED')),
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(buyer_identity_id,release_id)
    )""",
    """CREATE TABLE IF NOT EXISTS oap_music_purchase_splits (
        split_id UUID PRIMARY KEY,
        entitlement_id UUID NOT NULL
            REFERENCES oap_music_purchase_entitlements(entitlement_id)
            ON DELETE RESTRICT,
        beneficiary_identity_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
        split_kind TEXT NOT NULL
            CHECK (split_kind IN ('ARTIST','COLLABORATOR','OAP')),
        basis_points INTEGER NOT NULL CHECK (basis_points BETWEEN 1 AND 10000),
        amount_minor BIGINT NOT NULL CHECK (amount_minor >= 0),
        state TEXT NOT NULL DEFAULT 'PAYOUT_PROVIDER_REQUIRED'
            CHECK (state IN ('PAYOUT_PROVIDER_REQUIRED','PAID_EXTERNALLY','DISPUTED','REVERSED')),
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(entitlement_id,beneficiary_identity_id,split_kind)
    )""",
    """CREATE INDEX IF NOT EXISTS ix_music_entitlement_buyer_created
       ON oap_music_purchase_entitlements(buyer_identity_id,created_at DESC)""",
)

MIGRATION_CHECKSUM = hashlib.sha256(
    "\n".join(SCHEMA_STATEMENTS).encode()
).hexdigest()

VALID_SPLIT_KINDS = {"ARTIST", "COLLABORATOR", "OAP"}


def _uuid(value: object, name: str) -> str:
    try:
        return str(UUID(str(value)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError(f"invalid_{name}") from exc


def _split_plan(value: Iterable[Mapping[str, object]]) -> tuple[dict[str, Any], ...]:
    rows: list[dict[str, Any]] = []
    total = 0
    seen: set[tuple[str, str]] = set()
    for raw in value:
        beneficiary = _uuid(raw.get("beneficiary_identity_id"), "beneficiary_identity_id")
        kind = str(raw.get("split_kind") or "").strip().upper()
        if kind not in VALID_SPLIT_KINDS:
            raise ValueError("invalid_split_kind")
        try:
            bps = int(raw.get("basis_points"))
        except (TypeError, ValueError) as exc:
            raise ValueError("invalid_basis_points") from exc
        if not 1 <= bps <= 10000:
            raise ValueError("invalid_basis_points")
        key = (beneficiary, kind)
        if key in seen:
            raise ValueError("duplicate_split_beneficiary")
        seen.add(key)
        total += bps
        rows.append(
            {
                "beneficiary_identity_id": beneficiary,
                "split_kind": kind,
                "basis_points": bps,
            }
        )
    if not rows or total != 10000:
        raise ValueError("split_plan_must_total_10000_basis_points")
    return tuple(rows)


def _allocate(amount_minor: int, plan: tuple[dict[str, Any], ...]) -> tuple[dict[str, Any], ...]:
    remaining = amount_minor
    result: list[dict[str, Any]] = []
    for index, item in enumerate(plan):
        amount = (
            remaining
            if index == len(plan) - 1
            else (amount_minor * int(item["basis_points"])) // 10000
        )
        remaining -= amount
        result.append({**item, "amount_minor": amount})
    return tuple(result)


def validate_order_terms(
    *,
    listing_price_minor: object,
    requested_price_minor: object,
    minimum_price_minor: object = 100,
    optional_pay_more: bool = True,
    quantity: object = 1,
) -> int:
    """Validate non-live Music purchase pricing and return the unit price.

    This performs no payment, settlement, fulfilment, or external call.
    """
    try:
        listing = int(listing_price_minor)
        minimum = int(minimum_price_minor)
        qty = int(quantity)
    except (TypeError, ValueError) as exc:
        raise ValueError("invalid_music_order_terms") from exc
    if qty != 1:
        raise ValueError("music_purchase_quantity_must_be_one")
    if listing < minimum or minimum < 100:
        raise ValueError("music_minimum_price_is_one_gbp")
    if requested_price_minor in (None, ""):
        return listing
    try:
        requested = int(requested_price_minor)
    except (TypeError, ValueError) as exc:
        raise ValueError("invalid_music_price") from exc
    if requested < minimum or requested < listing:
        raise ValueError("music_price_below_allowed_floor")
    if requested > listing and not optional_pay_more:
        raise ValueError("music_pay_more_disabled")
    return requested


def validate_finalize_terms(
    *,
    currency: object,
    unit_price_minor: object,
    subtotal_minor: object,
    minimum_price_minor: object,
    quantity: object,
    link_state: object,
    payment_state: object,
) -> None:
    """Fail closed before ownership is minted from existing Commerce evidence."""
    try:
        unit_price = int(unit_price_minor)
        subtotal = int(subtotal_minor)
        minimum = int(minimum_price_minor)
        qty = int(quantity)
    except (TypeError, ValueError) as exc:
        raise ValueError("invalid_music_finalize_terms") from exc
    if qty != 1:
        raise ValueError("music_purchase_quantity_must_be_one")
    if str(currency) != "GBP" or minimum < 100:
        raise ValueError("music_purchase_currency_or_floor_invalid")
    if unit_price < minimum or subtotal < unit_price:
        raise ValueError("music_purchase_price_invalid")
    if str(link_state) != "READY":
        raise ValueError("music_market_product_not_ready")
    if str(payment_state) != "CAPTURED":
        raise ValueError("payment_not_captured")


def init_schema(*, assume_yes: bool = False) -> dict[str, Any]:
    if not assume_yes:
        raise RuntimeError("explicit_confirmation_required")
    with postgres_db.connect() as connection:
        connection.execute("SELECT pg_advisory_xact_lock(%s)", (25800014,))
        row = connection.execute(
            "SELECT checksum FROM oap_schema_migrations WHERE version=%s",
            (MIGRATION_VERSION,),
        ).fetchone()
        if row is not None and str(row[0]) != MIGRATION_CHECKSUM:
            raise RuntimeError("music_market_purchase_migration_checksum_mismatch")
        if row is None:
            for statement in SCHEMA_STATEMENTS:
                connection.execute(statement)
            connection.execute(
                "INSERT INTO oap_schema_migrations(version,checksum) VALUES (%s,%s)",
                (MIGRATION_VERSION, MIGRATION_CHECKSUM),
            )
        connection.commit()
    return {"migration": MIGRATION_VERSION, "schema_ready": True}


class MusicMarketPurchaseStore:
    def link_release_product(
        self,
        *,
        seller_identity_id: object,
        release_id: object,
        product_id: object,
        rights_evidence_receipt_id: object,
        split_plan: Iterable[Mapping[str, object]],
        optional_pay_more: bool = True,
    ) -> dict[str, Any]:
        seller = _uuid(seller_identity_id, "seller_identity_id")
        release = _uuid(release_id, "release_id")
        product = _uuid(product_id, "product_id")
        receipt = _uuid(rights_evidence_receipt_id, "rights_evidence_receipt_id")
        plan = _split_plan(split_plan)
        link_id = str(uuid4())

        with postgres_db.connect() as connection:
            release_row = connection.execute(
                """SELECT rights_status,state FROM oap_music_releases
                   WHERE release_id=%s AND owner_identity_id=%s FOR SHARE""",
                (release, seller),
            ).fetchone()
            if release_row is None:
                raise PermissionError("music_release_not_owned")
            if str(release_row[0]) != "VERIFIED" or str(release_row[1]) not in {
                "APPROVED", "PUBLISHED"
            }:
                raise ValueError("music_release_not_sale_ready")
            product_row = connection.execute(
                """SELECT price_minor,currency,active FROM products
                   WHERE id=%s AND seller_id=%s FOR SHARE""",
                (product, seller),
            ).fetchone()
            if product_row is None or not bool(product_row[2]):
                raise ValueError("market_product_unavailable")
            price = int(product_row[0])
            if str(product_row[1]) != "GBP":
                raise ValueError("music_sale_requires_gbp")
            if price < 100:
                raise ValueError("music_minimum_price_is_one_gbp")
            evidence = connection.execute(
                """SELECT 1 FROM oap_music_evidence_receipts
                   WHERE receipt_id=%s AND owner_identity_id=%s AND release_id=%s""",
                (receipt, seller, release),
            ).fetchone()
            if evidence is None:
                raise PermissionError("rights_evidence_receipt_not_owned")
            for split in plan:
                active = connection.execute(
                    "SELECT 1 FROM users WHERE id=%s AND status='active'",
                    (split["beneficiary_identity_id"],),
                ).fetchone()
                if active is None:
                    raise ValueError("split_beneficiary_inactive")
            row = connection.execute(
                """INSERT INTO oap_music_market_products(
                       music_market_product_id,seller_identity_id,release_id,product_id,
                       rights_evidence_receipt_id,minimum_price_minor,optional_pay_more,
                       split_plan,state)
                   VALUES (%s,%s,%s,%s,%s,100,%s,%s::jsonb,'READY')
                   ON CONFLICT (release_id) DO UPDATE SET
                       rights_evidence_receipt_id=EXCLUDED.rights_evidence_receipt_id,
                       split_plan=EXCLUDED.split_plan,
                       optional_pay_more=EXCLUDED.optional_pay_more,
                       state='READY'
                   WHERE oap_music_market_products.product_id=EXCLUDED.product_id
                     AND oap_music_market_products.seller_identity_id=EXCLUDED.seller_identity_id
                   RETURNING music_market_product_id,minimum_price_minor,
                             optional_pay_more,state""",
                (
                    link_id, seller, release, product, receipt, bool(optional_pay_more),
                    json.dumps(plan),
                ),
            ).fetchone()
            if row is None:
                raise ValueError("music_market_product_conflict")
            connection.commit()
        return {
            "music_market_product_id": str(row[0]),
            "release_id": release,
            "product_id": product,
            "minimum_price_minor": int(row[1]),
            "optional_pay_more": bool(row[2]),
            "state": str(row[3]),
            "payment_capture_performed": False,
            "payout_performed": False,
        }

    def finalize_captured_order(
        self,
        *,
        buyer_identity_id: object,
        order_id: object,
    ) -> dict[str, Any]:
        buyer = _uuid(buyer_identity_id, "buyer_identity_id")
        order = _uuid(order_id, "order_id")

        with postgres_db.connect() as connection:
            row = connection.execute(
                """SELECT o.seller_identity_id,o.currency,o.subtotal_minor,
                          i.product_id,i.quantity,i.unit_price_minor,
                          p.intent_id,p.state,
                          mm.music_market_product_id,mm.release_id,mm.minimum_price_minor,
                          mm.split_plan,mm.state
                   FROM oap_commerce_orders o
                   JOIN oap_commerce_order_items i ON i.order_id=o.order_id
                   JOIN oap_commerce_payment_intents p ON p.order_id=o.order_id
                   JOIN oap_music_market_products mm ON mm.product_id=i.product_id
                   WHERE o.order_id=%s AND o.buyer_identity_id=%s
                   FOR UPDATE OF o,p,mm""",
                (order, buyer),
            ).fetchone()
            if row is None:
                raise PermissionError("music_order_not_owned_or_linked")
            seller = str(row[0])
            currency = str(row[1])
            subtotal = int(row[2])
            quantity = int(row[4])
            unit_price = int(row[5])
            payment_state = str(row[7])
            link_id = str(row[8])
            release = str(row[9])
            minimum = int(row[10])
            plan = tuple(dict(item) for item in row[11])
            link_state = str(row[12])
            validate_finalize_terms(
                currency=currency,
                unit_price_minor=unit_price,
                subtotal_minor=subtotal,
                minimum_price_minor=minimum,
                quantity=quantity,
                link_state=link_state,
                payment_state=payment_state,
            )

            existing = connection.execute(
                """SELECT entitlement_id,state,amount_minor,currency
                   FROM oap_music_purchase_entitlements WHERE order_id=%s""",
                (order,),
            ).fetchone()
            if existing is None:
                entitlement_id = str(uuid4())
                ent = connection.execute(
                    """INSERT INTO oap_music_purchase_entitlements(
                           entitlement_id,buyer_identity_id,seller_identity_id,
                           music_market_product_id,release_id,order_id,amount_minor,currency,state)
                       VALUES (%s,%s,%s,%s,%s,%s,%s,'GBP','OWNED')
                       RETURNING entitlement_id,state,amount_minor,currency""",
                    (entitlement_id,buyer,seller,link_id,release,order,subtotal),
                ).fetchone()
                allocations = _allocate(subtotal, plan)
                for allocation in allocations:
                    connection.execute(
                        """INSERT INTO oap_music_purchase_splits(
                               split_id,entitlement_id,beneficiary_identity_id,split_kind,
                               basis_points,amount_minor,state)
                           VALUES (%s,%s,%s,%s,%s,%s,'PAYOUT_PROVIDER_REQUIRED')""",
                        (
                            str(uuid4()), entitlement_id,
                            allocation["beneficiary_identity_id"],
                            allocation["split_kind"], allocation["basis_points"],
                            allocation["amount_minor"],
                        ),
                    )
            else:
                ent = existing
            connection.commit()

        return {
            "entitlement_id": str(ent[0]),
            "release_id": release,
            "order_id": order,
            "state": str(ent[1]),
            "amount_minor": int(ent[2]),
            "currency": str(ent[3]),
            "ownership_granted": str(ent[1]) == "OWNED",
            "payment_capture_performed_here": False,
            "payout_performed": False,
            "split_state": "PAYOUT_PROVIDER_REQUIRED",
        }

    def library(self, *, buyer_identity_id: object) -> list[dict[str, Any]]:
        buyer = _uuid(buyer_identity_id, "buyer_identity_id")
        with postgres_db.connect(readonly=True) as connection:
            rows = connection.execute(
                """SELECT e.entitlement_id,e.release_id,r.title,r.release_type,
                          e.order_id,e.amount_minor,e.currency,e.state,e.created_at
                   FROM oap_music_purchase_entitlements e
                   JOIN oap_music_releases r ON r.release_id=e.release_id
                   WHERE e.buyer_identity_id=%s
                   ORDER BY e.created_at DESC""",
                (buyer,),
            ).fetchall()
        return [
            {
                "entitlement_id": str(row[0]),
                "release_id": str(row[1]),
                "title": str(row[2]),
                "release_type": str(row[3]),
                "order_id": str(row[4]),
                "amount_minor": int(row[5]),
                "currency": str(row[6]),
                "state": str(row[7]),
                "created_at": row[8].isoformat(),
            }
            for row in rows
        ]

    def split_ledger(
        self, *, identity_id: object, entitlement_id: object
    ) -> list[dict[str, Any]]:
        identity = _uuid(identity_id, "identity_id")
        entitlement = _uuid(entitlement_id, "entitlement_id")
        with postgres_db.connect(readonly=True) as connection:
            owned = connection.execute(
                """SELECT 1 FROM oap_music_purchase_entitlements
                   WHERE entitlement_id=%s
                     AND (buyer_identity_id=%s OR seller_identity_id=%s)""",
                (entitlement, identity, identity),
            ).fetchone()
            if owned is None:
                raise PermissionError("music_entitlement_not_visible")
            rows = connection.execute(
                """SELECT split_id,beneficiary_identity_id,split_kind,basis_points,
                          amount_minor,state,created_at
                   FROM oap_music_purchase_splits
                   WHERE entitlement_id=%s ORDER BY split_kind,split_id""",
                (entitlement,),
            ).fetchall()
        return [
            {
                "split_id": str(row[0]),
                "beneficiary_identity_id": str(row[1]),
                "split_kind": str(row[2]),
                "basis_points": int(row[3]),
                "amount_minor": int(row[4]),
                "state": str(row[5]),
                "created_at": row[6].isoformat(),
            }
            for row in rows
        ]


STORE = MusicMarketPurchaseStore()
