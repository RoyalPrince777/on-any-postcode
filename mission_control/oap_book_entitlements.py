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
