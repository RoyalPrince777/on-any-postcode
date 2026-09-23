"""Prove owner isolation, publication rights and excerpt-only access."""

from datetime import datetime, timedelta, timezone

from mission_control.oap_book_access import Access, Book, Rotation
from mission_control.oap_book_delivery import (
    PurchaseReceipt,
    authorize_read,
)
from mission_control.oap_book_publication import EditionEvidence

NOW = datetime(2026, 9, 23, tzinfo=timezone.utc)


def edition(**changes):
    values = {
        "book_id": "premium", "edition_id": "v1", "manuscript_sha256": "hash",
        "creator_id": "creator", "publisher_authority_id": "authority",
        "rights_record_id": "rights", "founder_approval_id": "approval",
        "rights_verified": True, "manuscript_approved": True,
        "public_release_approved": True,
    }
    values.update(changes)
    return EditionEvidence(**values)


def read(**changes):
    values = {
        "book": Book("premium", premium=True),
        "edition": edition(),
        "authenticated_user_id": "member",
        "private_owner_id": None,
        "receipt": None,
        "rotation": None,
        "now": NOW,
    }
    values.update(changes)
    return authorize_read(**values)


def receipt(**changes):
    values = {
        "owner_id": "member", "book_id": "premium",
        "edition_id": "v1", "payment_receipt_id": "verified-reference",
        "payment_verified": True,
    }
    values.update(changes)
    return PurchaseReceipt(**values)


def test_owner_scoped_verified_purchase():
    assert read(receipt=receipt()).access is Access.PURCHASED
    for altered in (
        {"owner_id": "stranger"}, {"book_id": "other"},
        {"edition_id": "v2"}, {"payment_receipt_id": ""},
        {"payment_verified": False}, {"revoked": True},
    ):
        assert read(receipt=receipt(**altered)).access is Access.DENIED


def test_no_full_access_from_anonymous_or_client_preview():
    assert read(authenticated_user_id=None, receipt=receipt()).access is Access.DENIED
    preview = read(preview=True)
    assert preview.access is Access.PREVIEW
    assert preview.reason == "excerpt_only"


def test_rights_and_edition_mismatch_block_all_content():
    assert read(edition=edition(rights_verified=False),
                receipt=receipt(), preview=True).access is Access.DENIED
    assert read(edition=edition(book_id="different"),
                receipt=receipt()).access is Access.DENIED
    assert read(edition=edition(expires_at=NOW),
                receipt=receipt()).access is Access.DENIED


def test_core_free_only_when_edition_published():
    core = Book("premium", core_free=True)
    assert read(book=core).access is Access.FREE
    assert read(book=core, edition=edition(
        manuscript_approved=False,
    )).access is Access.DENIED


def test_rotation_expiry_does_not_revoke_verified_purchase():
    book = Book(
        "premium", premium=True, rights_evidence="written-grant",
        rights_allow_rotation=True,
    )
    rotation = Rotation("premium", NOW, NOW + timedelta(days=7))
    assert read(book=book, rotation=rotation).access is Access.ROTATION
    assert read(book=book, rotation=rotation,
                now=NOW + timedelta(days=7)).access is Access.DENIED
    assert read(book=book, rotation=rotation, receipt=receipt(),
                now=NOW + timedelta(days=7)).access is Access.PURCHASED


def test_private_owner_only_even_with_payment_or_preview():
    private = Book("premium", private=True)
    private_edition = edition(private=True, public_release_approved=False)
    assert read(book=private, edition=private_edition,
                private_owner_id="member").access is Access.PURCHASED
    assert read(book=private, edition=private_edition,
                private_owner_id="other", receipt=receipt(),
                preview=True).access is Access.DENIED
    assert read(book=private, edition=private_edition,
                private_owner_id="member",
                authenticated_user_id=None).access is Access.DENIED
