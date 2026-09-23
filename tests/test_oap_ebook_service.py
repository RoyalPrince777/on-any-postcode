"""Isolated ebook orchestration never trusts request-supplied purchase claims."""

from datetime import datetime, timedelta, timezone

import pytest

from mission_control import oap_ebook_service as service
from mission_control.oap_book_access import Book, Rotation
from mission_control.oap_book_delivery import PurchaseReceipt
from mission_control.oap_book_publication import EditionEvidence
from mission_control.oap_ebook_reader import EbookEdition, manuscript_digest

NOW = datetime(2026, 9, 23, tzinfo=timezone.utc)
PAGES = ("one", "two")
HASH = manuscript_digest(PAGES)
MANUSCRIPT = EbookEdition("oap", "v1", HASH, PAGES, frozenset({0}))
APPROVAL = EditionEvidence(
    "oap", "v1", HASH, "creator", "publisher", "rights", "founder",
    rights_verified=True, manuscript_approved=True,
    public_release_approved=True,
)


def read(**kwargs):
    args = {
        "book": Book("oap", premium=True),
        "approval": APPROVAL,
        "manuscript": MANUSCRIPT,
        "authenticated_identity": None,
        "private_owner_id": None,
        "rotation": None,
        "now": NOW,
        "page_number": 0,
    }
    args.update(kwargs)
    return service.read_ebook_page(**args)


def test_free_core_reads_without_purchase_query(monkeypatch):
    def impossible(**_kwargs):
        raise AssertionError("must not query paid entitlements for free core")

    monkeypatch.setattr(service, "lookup_verified_purchase", impossible)
    assert read(book=Book("oap", core_free=True)).content == "one"


def test_approved_hash_must_match_real_book(monkeypatch):
    monkeypatch.setattr(service, "lookup_verified_purchase", lambda **_: None)
    altered = EbookEdition("oap", "v1", "a" * 64, PAGES)
    with pytest.raises(PermissionError, match="manuscript_approval_mismatch"):
        read(manuscript=altered)
    with pytest.raises(PermissionError, match="manuscript_approval_mismatch"):
        read(approval=EditionEvidence(
            "oap", "different", HASH, "creator", "publisher",
            "rights", "founder",
        ))


def test_verified_owner_purchase_read_only(monkeypatch):
    observed = []

    def lookup(**kwargs):
        observed.append(kwargs)
        return PurchaseReceipt(
            owner_id=kwargs["authenticated_identity_id"],
            book_id=kwargs["book_id"],
            edition_id=kwargs["edition_id"],
            payment_receipt_id="verified-receipt",
            payment_verified=True,
        )

    monkeypatch.setattr(service, "lookup_verified_purchase", lookup)
    assert read(authenticated_identity="member", page_number=1).content == "two"
    assert observed == [{
        "authenticated_identity_id": "member",
        "book_id": "oap", "edition_id": "v1",
    }]


def test_missing_purchase_denied(monkeypatch):
    monkeypatch.setattr(service, "lookup_verified_purchase", lambda **_: None)
    with pytest.raises(PermissionError, match="access_denied"):
        read(authenticated_identity="member")


def test_unavailable_purchase_store_denies(monkeypatch):
    def unavailable(**_kwargs):
        raise RuntimeError("store offline")

    monkeypatch.setattr(service, "lookup_verified_purchase", unavailable)
    with pytest.raises(RuntimeError, match="store offline"):
        read(authenticated_identity="member")


def test_rotation_expires_at_every_page(monkeypatch):
    monkeypatch.setattr(service, "lookup_verified_purchase", lambda **_: None)
    book = Book(
        "oap", premium=True, rights_evidence="grant",
        rights_allow_rotation=True,
    )
    rotation = Rotation("oap", NOW, NOW + timedelta(days=7))
    assert read(book=book, rotation=rotation, page_number=1).content == "two"
    with pytest.raises(PermissionError, match="access_denied"):
        read(
            book=book, rotation=rotation,
            now=NOW + timedelta(days=7),
        )


def test_private_library_never_uses_paid_purchase_lookup(monkeypatch):
    def impossible(**_kwargs):
        raise AssertionError("private owner must not use paid lookup")

    monkeypatch.setattr(service, "lookup_verified_purchase", impossible)
    private = Book("oap", private=True)
    approval = EditionEvidence(
        "oap", "v1", HASH, "creator", "publisher", "rights", "founder",
        manuscript_approved=True, private=True,
    )
    assert read(
        book=private, approval=approval,
        authenticated_identity="owner", private_owner_id="owner",
    ).content == "one"
    with pytest.raises(PermissionError, match="access_denied"):
        read(
            book=private, approval=approval,
            authenticated_identity="other", private_owner_id="owner",
        )


def test_preview_is_excerpt_only(monkeypatch):
    monkeypatch.setattr(service, "lookup_verified_purchase", lambda **_: None)
    assert read(preview=True).content == "one"
    with pytest.raises(PermissionError, match="preview_page_denied"):
        read(preview=True, page_number=1)
