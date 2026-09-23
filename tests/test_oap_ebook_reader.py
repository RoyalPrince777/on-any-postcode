"""Ebook contract regressions; no live files or purchase execution."""

from datetime import datetime, timedelta, timezone

import pytest

from mission_control.oap_book_access import Access
from mission_control.oap_book_delivery import ReadingGrant
from mission_control.oap_ebook_reader import (
    EbookEdition,
    deliver_page,
    manuscript_digest,
    protected_reader_headers,
)

PAGES = ("chapter one", "chapter two", "chapter three")
NOW = datetime(2026, 9, 23, tzinfo=timezone.utc)
BOOK = EbookEdition(
    book_id="oap-book", edition_id="first", manuscript_sha256=manuscript_digest(PAGES),
    pages=PAGES,
    preview_pages=frozenset({0}),
)


def grant(access=Access.PURCHASED, **changes):
    values = {
        "access": access, "book_id": BOOK.book_id,
        "edition_id": BOOK.edition_id,
    }
    values.update(changes)
    return ReadingGrant(**values)


def page(access=Access.PURCHASED, **changes):
    values = {
        "edition": BOOK, "grant": grant(access),
        "authenticated_identity": "member-id", "page_number": 0, "now": NOW,
    }
    values.update(changes)
    return deliver_page(**values)


def test_owner_watermark_and_single_page():
    result = page()
    assert result.content == "chapter one"
    assert "member:" in result.watermark
    assert "member-id" not in result.watermark
    assert result.expires_at is None


def test_preview_cannot_leak_other_pages():
    excerpt = grant(Access.PREVIEW, reason="excerpt_only")
    assert page(grant=excerpt, authenticated_identity=None).content == "chapter one"
    for index in (1, 2):
        with pytest.raises(PermissionError, match="preview_page_denied"):
            page(grant=excerpt, page_number=index)
    with pytest.raises(PermissionError, match="preview_source_unverified"):
        page(grant=grant(Access.PREVIEW))


@pytest.mark.parametrize("access", (Access.PURCHASED, Access.ROTATION))
def test_paid_and_rotation_require_member(access):
    with pytest.raises(PermissionError, match="identity_required"):
        page(grant=grant(access), authenticated_identity=None)


def test_rotation_expiration_is_explicit():
    expiry = datetime(2026, 9, 28, tzinfo=timezone.utc)
    result = page(grant=grant(Access.ROTATION, expires_at=expiry))
    assert result.expires_at == expiry.isoformat()


@pytest.mark.parametrize("invalid", (-1, 3, True, "0"))
def test_invalid_pages_rejected(invalid):
    with pytest.raises(PermissionError):
        page(page_number=invalid)


def test_wrong_edition_denied():
    with pytest.raises(PermissionError, match="edition_unavailable"):
        page(grant=grant(book_id="other"))


def test_denied_grant_rejected():
    with pytest.raises(PermissionError, match="access_denied"):
        page(grant=grant(Access.DENIED))


def test_missing_digest_and_oversize_denied():
    with pytest.raises(PermissionError, match="edition_unavailable"):
        page(edition=EbookEdition("oap-book", "first", "", ("page",)))
    with pytest.raises(PermissionError, match="edition_unavailable"):
        page(edition=EbookEdition(
            "oap-book", "first", "a" * 64, ("x" * 12001,),
        ))


def test_protected_web_headers_do_not_claim_capture_proof():
    headers = protected_reader_headers()
    assert "no-store" in headers["Cache-Control"]
    assert "display-capture=()" in headers["Permissions-Policy"]
    assert "frame-ancestors 'none'" in headers["Content-Security-Policy"]


def test_rotation_requires_unexpired_trusted_clock():
    expiry = datetime(2026, 9, 28, tzinfo=timezone.utc)
    rotated = grant(Access.ROTATION, expires_at=expiry)
    with pytest.raises(PermissionError, match="rotation_expired"):
        page(grant=rotated, now=expiry)
    with pytest.raises(PermissionError, match="rotation_expired"):
        page(grant=rotated, now=expiry + timedelta(seconds=1))
    with pytest.raises(PermissionError, match="rotation_expired"):
        page(grant=grant(Access.ROTATION))
    with pytest.raises(PermissionError, match="clock_unavailable"):
        page(now=NOW.replace(tzinfo=None))


def test_manuscript_content_must_match_approved_digest():
    tampered = EbookEdition(
        "oap-book", "first", BOOK.manuscript_sha256,
        ("changed page", "chapter two", "chapter three"),
    )
    with pytest.raises(PermissionError, match="manuscript_integrity_failed"):
        page(edition=tampered)


def test_purchase_not_revoked_by_rotation_expiry():
    past = NOW - timedelta(days=7)
    assert page(grant=grant(Access.PURCHASED, expires_at=past)).content == "chapter one"
