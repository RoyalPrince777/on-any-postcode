"""First-party read-only purchase entitlement lookup and unapplied schema plan.

No schema creation, payment execution or entitlement grants happen on import.
Only a separate audited payment-confirmation workflow may create verified rows.
"""
from __future__ import annotations

import uuid

from . import postgres_db
from .oap_book_delivery import PurchaseReceipt

SCHEMA_VERSION = "oap_book_entitlements_v1"
SCHEMA_SQL = (
    """CREATE TABLE IF NOT EXISTS oap_book_entitlements (
        entitlement_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        identity_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        book_id TEXT NOT NULL CHECK (char_length(book_id) BETWEEN 1 AND 160),
        edition_id TEXT NOT NULL CHECK (char_length(edition_id) BETWEEN 1 AND 160),
        payment_receipt_id TEXT NOT NULL UNIQUE
            CHECK (char_length(payment_receipt_id) BETWEEN 1 AND 256),
        payment_verified BOOLEAN NOT NULL DEFAULT FALSE,
        revoked BOOLEAN NOT NULL DEFAULT FALSE,
        verification_receipt_id TEXT NOT NULL
            CHECK (char_length(verification_receipt_id) BETWEEN 1 AND 256),
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        UNIQUE (identity_id, book_id, edition_id, payment_receipt_id)
    )""",
    """CREATE INDEX IF NOT EXISTS idx_oap_book_entitlements_owner
        ON oap_book_entitlements(identity_id, book_id, edition_id)""",
)


class BookEntitlementsUnavailable(RuntimeError):
    """Trusted entitlement store could not be read safely."""


def schema_plan() -> dict[str, object]:
    """Return schema for independent review; never execute a migration."""
    return {"version": SCHEMA_VERSION, "statements": SCHEMA_SQL, "applied": False}


def lookup_verified_purchase(
    *,
    authenticated_identity_id: str,
    book_id: str,
    edition_id: str,
) -> PurchaseReceipt | None:
    """Read one owner-scoped independently verified receipt, never write one."""
    try:
        identity = str(uuid.UUID(authenticated_identity_id))
    except (ValueError, TypeError, AttributeError) as exc:
        raise ValueError("invalid_authenticated_identity") from exc
    if not isinstance(book_id, str) or not 1 <= len(book_id) <= 160:
        raise ValueError("invalid_book_id")
    if not isinstance(edition_id, str) or not 1 <= len(edition_id) <= 160:
        raise ValueError("invalid_edition_id")
    try:
        with postgres_db.connect(readonly=True) as connection:
            row = connection.execute(
                """SELECT payment_receipt_id
                   FROM oap_book_entitlements
                   WHERE identity_id=%s AND book_id=%s AND edition_id=%s
                     AND payment_verified IS TRUE AND revoked IS FALSE
                     AND verification_receipt_id <> ''
                   ORDER BY created_at DESC LIMIT 1""",
                (identity, book_id, edition_id),
            ).fetchone()
    except Exception as exc:
        raise BookEntitlementsUnavailable("entitlement_read_failed") from exc
    if not row:
        return None
    receipt_id = str(row[0])
    if not receipt_id:
        raise BookEntitlementsUnavailable("invalid_verification_receipt")
    return PurchaseReceipt(
        owner_id=identity,
        book_id=book_id,
        edition_id=edition_id,
        payment_receipt_id=receipt_id,
        payment_verified=True,
    )



def list_verified_purchases(*, authenticated_identity_id: str) -> tuple[dict[str, object], ...]:
    """List only durable, non-revoked ebook entitlements owned by one member.

    This is a read projection. It never creates ownership and never trusts
    browser-supplied payment state.
    """
    try:
        identity = str(uuid.UUID(authenticated_identity_id))
    except (ValueError, TypeError, AttributeError) as exc:
        raise ValueError("invalid_authenticated_identity") from exc
    try:
        with postgres_db.connect(readonly=True) as connection:
            rows = connection.execute(
                """SELECT e.entitlement_id,e.book_id,e.edition_id,
                          e.payment_receipt_id,e.verification_receipt_id,e.created_at,
                          c.creator_id,c.publisher_authority_id,c.manuscript_sha256
                   FROM oap_book_entitlements e
                   JOIN oap_ebook_editions c
                     ON c.book_id=e.book_id AND c.edition_id=e.edition_id
                   WHERE e.identity_id=%s
                     AND e.payment_verified IS TRUE
                     AND e.revoked IS FALSE
                     AND e.verification_receipt_id <> ''
                     AND c.status='APPROVED'
                     AND c.public_release_approved IS TRUE
                   ORDER BY e.created_at DESC""",
                (identity,),
            ).fetchall()
    except Exception as exc:
        raise BookEntitlementsUnavailable("entitlement_library_read_failed") from exc
    return tuple(
        {
            "entitlement_id": str(row[0]),
            "book_id": str(row[1]),
            "edition_id": str(row[2]),
            "payment_receipt_id": str(row[3]),
            "verification_receipt_id": str(row[4]),
            "created_at": row[5].isoformat(),
            "creator_id": str(row[6]),
            "publisher_authority_id": str(row[7]),
            "manuscript_sha256": str(row[8]),
            "state": "OWNED",
        }
        for row in rows
    )



def grant_from_verified_capture(
    *,
    authenticated_identity_id: str,
    order_id: str,
) -> dict[str, object]:
    """Mint one ebook entitlement only from server-side captured-payment evidence.

    The caller supplies only identity and order. Payment state, provider receipt,
    product linkage, amount, rights and edition approval are resolved server-side.
    """
    try:
        identity = str(uuid.UUID(authenticated_identity_id))
        order = str(uuid.UUID(order_id))
    except (ValueError, TypeError, AttributeError) as exc:
        raise ValueError("invalid_entitlement_finalize_selector") from exc
    try:
        with postgres_db.connect() as connection:
            row = connection.execute(
                """SELECT o.seller_identity_id,o.currency,o.subtotal_minor,
                          i.product_id,i.quantity,i.unit_price_minor,
                          p.intent_id,p.state,p.provider_reference,
                          em.book_id,em.edition_id,em.state,
                          e.status,e.private,e.rights_verified,
                          e.manuscript_approved,e.public_release_approved,
                          r.receipt_id,r.provider_state,r.provider_reference
                   FROM oap_commerce_orders o
                   JOIN oap_commerce_order_items i ON i.order_id=o.order_id
                   JOIN oap_commerce_payment_intents p ON p.order_id=o.order_id
                   JOIN oap_ebook_market_products em ON em.product_id=i.product_id
                   JOIN oap_ebook_editions e
                     ON e.book_id=em.book_id AND e.edition_id=em.edition_id
                   JOIN oap_commerce_provider_receipts r
                     ON r.provider_reference=p.provider_reference
                    AND r.kind='payment_webhook'
                   WHERE o.order_id=%s AND o.buyer_identity_id=%s
                   ORDER BY r.created_at DESC
                   LIMIT 1
                   FOR UPDATE OF o,p,em""",
                (order, identity),
            ).fetchone()
            if row is None:
                raise PermissionError("ebook_order_not_owned_or_verified")

            currency = str(row[1])
            subtotal = int(row[2])
            quantity = int(row[4])
            unit_price = int(row[5])
            intent_id = str(row[6])
            payment_state = str(row[7])
            payment_provider_reference = str(row[8] or "")
            book_id = str(row[9])
            edition_id = str(row[10])
            market_state = str(row[11])
            edition_status = str(row[12])
            private = row[13] is True
            rights_verified = row[14] is True
            manuscript_approved = row[15] is True
            public_release_approved = row[16] is True
            verification_receipt_id = str(row[17])
            provider_state = str(row[18]).upper()
            receipt_provider_reference = str(row[19])

            if quantity != 1:
                raise ValueError("ebook_purchase_quantity_must_be_one")
            if currency != "GBP" or subtotal != unit_price or subtotal < 0:
                raise ValueError("ebook_purchase_terms_invalid")
            if payment_state != "CAPTURED":
                raise PermissionError("payment_not_captured")
            if not payment_provider_reference or (
                payment_provider_reference != receipt_provider_reference
            ):
                raise PermissionError("provider_reference_mismatch")
            if provider_state not in {"CAPTURED", "SETTLED", "SUCCEEDED"}:
                raise PermissionError("provider_capture_not_verified")
            if market_state != "ACTIVE":
                raise PermissionError("ebook_market_product_not_active")
            if (
                edition_status != "APPROVED"
                or private
                or not rights_verified
                or not manuscript_approved
                or not public_release_approved
            ):
                raise PermissionError("ebook_publication_not_approved")

            existing = connection.execute(
                """SELECT entitlement_id,revoked,payment_verified
                   FROM oap_book_entitlements
                   WHERE identity_id=%s AND book_id=%s AND edition_id=%s
                     AND payment_receipt_id=%s
                   LIMIT 1""",
                (identity, book_id, edition_id, intent_id),
            ).fetchone()
            if existing is None:
                entitlement = connection.execute(
                    """INSERT INTO oap_book_entitlements(
                           identity_id,book_id,edition_id,payment_receipt_id,
                           payment_verified,revoked,verification_receipt_id)
                       VALUES (%s,%s,%s,%s,TRUE,FALSE,%s)
                       RETURNING entitlement_id,revoked,payment_verified""",
                    (
                        identity,
                        book_id,
                        edition_id,
                        intent_id,
                        verification_receipt_id,
                    ),
                ).fetchone()
                if entitlement is None:
                    raise BookEntitlementsUnavailable("entitlement_create_failed")
                created = True
            else:
                entitlement = existing
                created = False
            connection.commit()
    except (PermissionError, ValueError):
        raise
    except BookEntitlementsUnavailable:
        raise
    except Exception as exc:
        raise BookEntitlementsUnavailable("entitlement_finalize_failed") from exc

    return {
        "entitlement_id": str(entitlement[0]),
        "book_id": book_id,
        "edition_id": edition_id,
        "order_id": order,
        "payment_receipt_id": intent_id,
        "verification_receipt_id": verification_receipt_id,
        "payment_verified": bool(entitlement[2]),
        "revoked": bool(entitlement[1]),
        "state": "OWNED" if bool(entitlement[2]) and not bool(entitlement[1]) else "BLOCKED",
        "created": created,
        "payment_capture_performed_here": False,
        "provider_called_here": False,
    }
