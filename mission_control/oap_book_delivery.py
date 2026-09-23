"""First-party book delivery decision, isolated from live routes and payments.

The caller must load the authenticated identity and independently verified
edition, grant and entitlement records from trusted storage. No request body
may supply these records to a public reader.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from .oap_book_access import Access, Book, Rotation, decide_access
from .oap_book_publication import EditionEvidence, publication_blocks


@dataclass(frozen=True)
class PurchaseReceipt:
    owner_id: str
    book_id: str
    edition_id: str
    payment_receipt_id: str
    payment_verified: bool = False
    revoked: bool = False


@dataclass(frozen=True)
class ReadingGrant:
    access: Access
    book_id: str
    edition_id: str
    expires_at: datetime | None = None
    reason: str = ""


def authorize_read(
    *,
    book: Book,
    edition: EditionEvidence,
    authenticated_user_id: str | None,
    private_owner_id: str | None,
    receipt: PurchaseReceipt | None,
    rotation: Rotation | None,
    now: datetime,
    preview: bool = False,
) -> ReadingGrant:
    """Allow full-page delivery only for FREE/PURCHASED/ROTATION grants.

    PREVIEW grants must use a distinct excerpt-only content source. This
    function never returns bytes, redirects or public storage paths.
    """
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("timezone_required")
    denied = ReadingGrant(Access.DENIED, book.book_id, edition.edition_id)
    if book.book_id != edition.book_id or not book.book_id or not edition.edition_id:
        return denied
    if book.private:
        if (
            authenticated_user_id is None
            or authenticated_user_id != private_owner_id
            or not edition.private
        ):
            return denied
        if not edition.manuscript_approved:
            return denied
        return ReadingGrant(Access.PURCHASED, book.book_id, edition.edition_id)
    if publication_blocks(edition, now=now):
        return denied
    purchased = frozenset()
    if (
        receipt is not None
        and authenticated_user_id
        and receipt.owner_id == authenticated_user_id
        and receipt.book_id == book.book_id
        and receipt.edition_id == edition.edition_id
        and bool(receipt.payment_receipt_id)
        and receipt.payment_verified
        and not receipt.revoked
    ):
        purchased = frozenset({book.book_id})
    result = decide_access(
        book,
        user_id=authenticated_user_id,
        purchased_book_ids=purchased,
        rotation=rotation,
        now=now,
        preview=preview,
    )
    return ReadingGrant(
        result.access, book.book_id, edition.edition_id,
        result.rotation_ends_at,
        "excerpt_only" if result.access is Access.PREVIEW else "",
    )
