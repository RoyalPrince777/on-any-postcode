"""Approved OAP ebook -> OAP Market product bridge.

This module creates no payment and grants no reading entitlement. A digital
ebook can enter Market only when the seller is a Certified Merchant and the
same owner has both an approved creator draft and an approved public catalogue
edition with verified rights and manuscript approval.
"""
from __future__ import annotations

import hashlib
import re
import uuid
from typing import Any

from . import postgres_db

MIGRATION_VERSION = "oap_ebook_market_v1"
_IDEMPOTENCY = re.compile(r"^[A-Za-z0-9._:-]{8,160}$")
SCHEMA_STATEMENTS = (
    """CREATE TABLE IF NOT EXISTS oap_ebook_market_products (
        book_id TEXT NOT NULL,
        edition_id TEXT NOT NULL,
        seller_identity_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
        product_id UUID NOT NULL UNIQUE REFERENCES products(id) ON DELETE RESTRICT,
        state TEXT NOT NULL DEFAULT 'ACTIVE'
            CHECK (state IN ('ACTIVE','STOPPED','REVOKED')),
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (book_id,edition_id),
        UNIQUE(seller_identity_id,book_id,edition_id)
    )""",
    """CREATE INDEX IF NOT EXISTS ix_ebook_market_seller
       ON oap_ebook_market_products(seller_identity_id,created_at DESC)""",
)
MIGRATION_CHECKSUM = hashlib.sha256("\n".join(SCHEMA_STATEMENTS).encode()).hexdigest()


class EbookMarketUnavailable(RuntimeError):
    pass


def init_schema(*, assume_yes: bool = False, dry_run: bool = False) -> dict[str, object]:
    if not assume_yes:
        raise RuntimeError("explicit_confirmation_required")
    if dry_run:
        return {
            "migration": MIGRATION_VERSION,
            "checksum": MIGRATION_CHECKSUM,
            "schema_ready": False,
            "dry_run": True,
        }
    try:
        with postgres_db.connect() as connection:
            for statement in SCHEMA_STATEMENTS:
                connection.execute(statement)
            connection.commit()
    except Exception as exc:
        raise EbookMarketUnavailable("ebook_market_schema_init_failed") from exc
    return {
        "migration": MIGRATION_VERSION,
        "checksum": MIGRATION_CHECKSUM,
        "schema_ready": True,
        "dry_run": False,
    }


def _uuid(value: object, field: str) -> str:
    try:
        return str(uuid.UUID(str(value)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError(f"invalid_{field}") from exc


def _selector(value: object, field: str) -> str:
    text = str(value or "").strip()
    if not 1 <= len(text) <= 160:
        raise ValueError(f"invalid_{field}")
    return text


def publish_approved_ebook(
    seller_identity_id: object,
    *,
    book_id: object,
    edition_id: object,
) -> dict[str, Any]:
    """Create one real Market product from already-approved digital evidence."""

    seller = _uuid(seller_identity_id, "seller_identity_id")
    book = _selector(book_id, "book_id")
    edition = _selector(edition_id, "edition_id")
    try:
        with postgres_db.connect() as connection:
            certified = connection.execute(
                """SELECT 1 FROM oap_identity_roles
                   WHERE identity_id=%s AND role_id='certified_merchant' LIMIT 1""",
                (seller,),
            ).fetchone()
            if certified is None:
                raise PermissionError("certified_merchant_required")

            existing = connection.execute(
                """SELECT product_id,state FROM oap_ebook_market_products
                   WHERE book_id=%s AND edition_id=%s AND seller_identity_id=%s
                   FOR UPDATE""",
                (book, edition, seller),
            ).fetchone()
            if existing is not None:
                return {
                    "book_id": book,
                    "edition_id": edition,
                    "product_id": str(existing[0]),
                    "state": str(existing[1]),
                    "created": False,
                    "payment_capture_performed": False,
                    "entitlement_issued": False,
                }

            evidence = connection.execute(
                """SELECT d.title,d.description,d.price_minor,d.manuscript_sha256
                   FROM oap_ebook_creator_drafts d
                   JOIN oap_ebook_editions e
                     ON e.book_id=d.book_id AND e.edition_id=d.edition_id
                   WHERE d.owner_identity_id=%s
                     AND d.book_id=%s AND d.edition_id=%s
                     AND d.state='APPROVED'
                     AND d.rights_attested IS TRUE
                     AND e.owner_id=%s
                     AND e.status='APPROVED'
                     AND e.private IS FALSE
                     AND e.rights_verified IS TRUE
                     AND e.manuscript_approved IS TRUE
                     AND e.public_release_approved IS TRUE
                     AND e.manuscript_sha256=d.manuscript_sha256
                   FOR SHARE OF d,e""",
                (seller, book, edition, seller),
            ).fetchone()
            if evidence is None:
                raise PermissionError("ebook_not_approved_for_market")

            title = str(evidence[0])
            description = str(evidence[1] or "")
            price_minor = evidence[2]
            if price_minor is None:
                raise ValueError("ebook_price_required")
            price_minor = int(price_minor)
            if not 0 <= price_minor <= 100_000_000:
                raise ValueError("ebook_price_invalid")

            product = connection.execute(
                """INSERT INTO products(
                       seller_id,name,description,price_minor,currency,active
                   ) VALUES (%s,%s,%s,%s,'GBP',TRUE)
                   RETURNING id""",
                (seller, title, description, price_minor),
            ).fetchone()
            if product is None:
                raise EbookMarketUnavailable("ebook_market_product_create_failed")
            product_id = str(product[0])
            connection.execute(
                """INSERT INTO oap_ebook_market_products(
                       book_id,edition_id,seller_identity_id,product_id,state
                   ) VALUES (%s,%s,%s,%s,'ACTIVE')""",
                (book, edition, seller, product_id),
            )
            connection.commit()
    except (PermissionError, ValueError):
        raise
    except EbookMarketUnavailable:
        raise
    except Exception as exc:
        raise EbookMarketUnavailable("ebook_market_publish_failed") from exc

    return {
        "book_id": book,
        "edition_id": edition,
        "product_id": product_id,
        "state": "ACTIVE",
        "created": True,
        "payment_capture_performed": False,
        "entitlement_issued": False,
    }



def public_product(book_id: object, edition_id: object) -> dict[str, Any] | None:
    """Return one public digital ebook product only when every gate is still valid."""

    book = _selector(book_id, "book_id")
    edition = _selector(edition_id, "edition_id")
    try:
        with postgres_db.connect(readonly=True) as connection:
            row = connection.execute(
                """SELECT m.book_id,m.edition_id,m.product_id,m.state,
                          p.name,p.description,p.price_minor,p.currency,
                          COALESCE(u.display_name,u.username),
                          e.creator_id,e.publisher_authority_id
                   FROM oap_ebook_market_products m
                   JOIN products p ON p.id=m.product_id
                   JOIN users u ON u.id=m.seller_identity_id
                   JOIN oap_ebook_editions e
                     ON e.book_id=m.book_id AND e.edition_id=m.edition_id
                   WHERE m.book_id=%s AND m.edition_id=%s
                     AND m.state='ACTIVE'
                     AND p.active=TRUE
                     AND u.status='active'
                     AND e.status='APPROVED'
                     AND e.private IS FALSE
                     AND e.rights_verified IS TRUE
                     AND e.manuscript_approved IS TRUE
                     AND e.public_release_approved IS TRUE
                   LIMIT 1""",
                (book, edition),
            ).fetchone()
    except Exception as exc:
        raise EbookMarketUnavailable("ebook_market_read_failed") from exc
    if row is None:
        return None
    return {
        "book_id": str(row[0]),
        "edition_id": str(row[1]),
        "product_id": str(row[2]),
        "state": str(row[3]),
        "title": str(row[4]),
        "description": str(row[5] or ""),
        "price_minor": int(row[6]),
        "currency": str(row[7]),
        "seller": str(row[8]),
        "creator_id": str(row[9]),
        "publisher_authority_id": str(row[10]),
        "physical_product": False,
        "payment_capture_performed": False,
    }



def create_unlock_intent(
    buyer_identity_id: object,
    *,
    book_id: object,
    edition_id: object,
    idempotency_key: object,
) -> dict[str, Any]:
    """Create a digital-only commerce order and payment intent.

    This performs no provider call, capture, fulfilment, entitlement issuance or
    ownership change. Reusing the same idempotency key with different terms fails.
    """

    buyer = _uuid(buyer_identity_id, "buyer_identity_id")
    book = _selector(book_id, "book_id")
    edition = _selector(edition_id, "edition_id")
    key = str(idempotency_key or "").strip()
    if not _IDEMPOTENCY.fullmatch(key):
        raise ValueError("invalid_idempotency_key")
    try:
        with postgres_db.connect() as connection:
            identity = connection.execute(
                """SELECT 1 FROM users u
                   JOIN oap_identities i ON i.identity_id=u.id
                   WHERE u.id=%s AND u.status='active' AND i.status='ACTIVE'
                   LIMIT 1""",
                (buyer,),
            ).fetchone()
            if identity is None:
                raise PermissionError("buyer_unavailable")

            listing = connection.execute(
                """SELECT m.product_id,m.seller_identity_id,p.name,p.price_minor,p.currency
                   FROM oap_ebook_market_products m
                   JOIN products p ON p.id=m.product_id
                   JOIN oap_ebook_editions e
                     ON e.book_id=m.book_id AND e.edition_id=m.edition_id
                   WHERE m.book_id=%s AND m.edition_id=%s
                     AND m.state='ACTIVE' AND p.active=TRUE
                     AND e.status='APPROVED' AND e.private IS FALSE
                     AND e.rights_verified IS TRUE
                     AND e.manuscript_approved IS TRUE
                     AND e.public_release_approved IS TRUE
                   FOR SHARE OF m,p,e""",
                (book, edition),
            ).fetchone()
            if listing is None:
                raise PermissionError("ebook_unavailable")
            product_id = str(listing[0])
            seller = str(listing[1])
            if seller == buyer:
                raise ValueError("cannot_unlock_own_ebook")
            title = str(listing[2])
            amount = int(listing[3])
            currency = str(listing[4])
            if currency != "GBP" or amount < 0:
                raise ValueError("ebook_price_invalid")

            existing = connection.execute(
                """SELECT o.order_id,o.state,o.currency,o.subtotal_minor,
                          i.product_id,i.quantity,p.intent_id,p.state
                   FROM oap_commerce_orders o
                   JOIN oap_commerce_order_items i ON i.order_id=o.order_id
                   JOIN oap_commerce_payment_intents p ON p.order_id=o.order_id
                   WHERE o.buyer_identity_id=%s AND o.idempotency_key=%s
                   LIMIT 1""",
                (buyer, key),
            ).fetchone()
            if existing is not None:
                if (
                    str(existing[2]) != currency
                    or int(existing[3]) != amount
                    or str(existing[4]) != product_id
                    or int(existing[5]) != 1
                ):
                    raise ValueError("idempotency_key_reused")
                order_id = str(existing[0])
                order_state = str(existing[1])
                intent_id = str(existing[6])
                intent_state = str(existing[7])
                created = False
            else:
                order = connection.execute(
                    """INSERT INTO oap_commerce_orders(
                           buyer_identity_id,seller_identity_id,state,currency,
                           subtotal_minor,idempotency_key)
                       VALUES (%s,%s,'PAYMENT_PROVIDER_REQUIRED',%s,%s,%s)
                       RETURNING order_id,state""",
                    (buyer, seller, currency, amount, key),
                ).fetchone()
                if order is None:
                    raise EbookMarketUnavailable("ebook_unlock_order_create_failed")
                order_id = str(order[0])
                order_state = str(order[1])
                connection.execute(
                    """INSERT INTO oap_commerce_order_items(
                           order_id,product_id,quantity,unit_price_minor,product_name)
                       VALUES (%s,%s,1,%s,%s)""",
                    (order_id, product_id, amount, title),
                )
                intent = connection.execute(
                    """INSERT INTO oap_commerce_payment_intents(
                           order_id,amount_minor,currency,state)
                       VALUES (%s,%s,%s,'PROVIDER_REQUIRED')
                       RETURNING intent_id,state""",
                    (order_id, amount, currency),
                ).fetchone()
                if intent is None:
                    raise EbookMarketUnavailable("ebook_unlock_payment_intent_failed")
                intent_id = str(intent[0])
                intent_state = str(intent[1])
                created = True
            connection.commit()
    except (PermissionError, ValueError):
        raise
    except EbookMarketUnavailable:
        raise
    except Exception as exc:
        raise EbookMarketUnavailable("ebook_unlock_intent_failed") from exc

    return {
        "book_id": book,
        "edition_id": edition,
        "product_id": product_id,
        "order_id": order_id,
        "order_state": order_state,
        "payment_intent_id": intent_id,
        "payment_state": intent_state,
        "created": created,
        "payment_capture_performed": False,
        "provider_called": False,
        "fulfilment_intent_created": False,
        "entitlement_issued": False,
        "ownership_granted": False,
    }
