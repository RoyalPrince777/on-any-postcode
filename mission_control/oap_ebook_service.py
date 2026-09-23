"""Isolated first-party ebook reader orchestration; not a live Flask route.

The trusted caller, never the request body, supplies authenticated identity,
the approved edition/manuscript, private owner, rights and rotation. Purchase
lookup reads owner-scoped records only. No live data is created or changed.
"""
from __future__ import annotations

from datetime import datetime

from .oap_book_access import Book, Rotation
from .oap_book_delivery import authorize_read
from .oap_book_entitlements import lookup_verified_purchase
from .oap_book_publication import EditionEvidence
from .oap_ebook_reader import EbookEdition, EbookPage, deliver_page


def read_ebook_page(
    *,
    book: Book,
    approval: EditionEvidence,
    manuscript: EbookEdition,
    authenticated_identity: str | None,
    private_owner_id: str | None,
    rotation: Rotation | None,
    now: datetime,
    page_number: int,
    preview: bool = False,
) -> EbookPage:
    """Enforce rights + manuscript binding before returning one reader page.

    The trusted caller must independently verify all edition approval flags and
    private owner identity; this module cannot validate a signature or payment
    merely by receiving a True flag. A purchase-store error fails closed.
    """
    if (
        book.book_id != approval.book_id
        or book.book_id != manuscript.book_id
        or approval.edition_id != manuscript.edition_id
        or approval.manuscript_sha256 != manuscript.manuscript_sha256
    ):
        raise PermissionError("manuscript_approval_mismatch")
    receipt = None
    if authenticated_identity and not book.private and not book.core_free:
        receipt = lookup_verified_purchase(
            authenticated_identity_id=authenticated_identity,
            book_id=book.book_id,
            edition_id=approval.edition_id,
        )
    grant = authorize_read(
        book=book,
        edition=approval,
        authenticated_user_id=authenticated_identity,
        private_owner_id=private_owner_id,
        receipt=receipt,
        rotation=rotation,
        now=now,
        preview=preview,
    )
    return deliver_page(
        edition=manuscript,
        grant=grant,
        authenticated_identity=authenticated_identity,
        page_number=page_number,
        now=now,
    )
