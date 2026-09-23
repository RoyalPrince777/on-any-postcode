"""Ebook page-delivery contract: authenticated, bounded and fail-closed.

This service is not a route, renderer or DRM. Trusted callers must fetch
manuscript pages from private storage AFTER authorisation. It never accepts
public file URLs and never returns a complete paid ebook for preview access.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone

from .oap_book_access import Access
from .oap_book_delivery import ReadingGrant

MAX_PAGE_CHARS = 12000
MAX_PAGES = 10000


@dataclass(frozen=True)
class EbookEdition:
    book_id: str
    edition_id: str
    manuscript_sha256: str
    pages: tuple[str, ...]
    preview_pages: frozenset[int] = frozenset()


@dataclass(frozen=True)
class EbookPage:
    number: int
    content: str
    watermark: str
    expires_at: str | None


def manuscript_digest(pages: tuple[str, ...]) -> str:
    """Hash exact, ordered UTF-8 page text with unambiguous framing."""
    canonical = json.dumps(
        pages, ensure_ascii=False, separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _watermark(identity: str, book_id: str, edition_id: str) -> str:
    identity_hash = hashlib.sha256(identity.encode("utf-8")).hexdigest()[:16]
    return f"OAP · {book_id} · {edition_id} · member:{identity_hash}"


def deliver_page(
    *,
    edition: EbookEdition,
    grant: ReadingGrant,
    authenticated_identity: str | None,
    page_number: int,
    now: datetime,
) -> EbookPage:
    """Deliver one numbered page; all preview content is allowlisted.

    Callers must generate no-store, frame-denying responses and re-authorise
    every request. Rotation expiry needs a fresh grant, not a cached token.
    """
    if now.tzinfo is None or now.utcoffset() is None:
        raise PermissionError("clock_unavailable")
    if not isinstance(page_number, int) or isinstance(page_number, bool):
        raise PermissionError("page_denied")
    if not (
        grant.book_id == edition.book_id
        and grant.edition_id == edition.edition_id
        and edition.book_id
        and edition.edition_id
        and len(edition.manuscript_sha256) == 64
        and 0 < len(edition.pages) <= MAX_PAGES
        and all(isinstance(page, str) and 0 < len(page) <= MAX_PAGE_CHARS
                for page in edition.pages)
        and 0 <= page_number < len(edition.pages)
    ):
        raise PermissionError("edition_unavailable")
    if manuscript_digest(edition.pages) != edition.manuscript_sha256:
        raise PermissionError("manuscript_integrity_failed")
    if grant.access is Access.ROTATION:
        expiry = grant.expires_at
        if (
            expiry is None
            or expiry.tzinfo is None
            or expiry.utcoffset() is None
            or now.astimezone(timezone.utc) >= expiry.astimezone(timezone.utc)
        ):
            raise PermissionError("rotation_expired")
    if grant.access is Access.DENIED:
        raise PermissionError("access_denied")
    if grant.access is Access.PREVIEW and page_number not in edition.preview_pages:
        raise PermissionError("preview_page_denied")
    if grant.access not in (
        Access.PREVIEW, Access.FREE, Access.PURCHASED, Access.ROTATION,
    ):
        raise PermissionError("access_denied")
    if grant.access in (Access.PURCHASED, Access.ROTATION) and not authenticated_identity:
        raise PermissionError("identity_required")
    if grant.access is Access.PREVIEW and grant.reason != "excerpt_only":
        raise PermissionError("preview_source_unverified")
    identity = authenticated_identity or "public-preview"
    return EbookPage(
        number=page_number,
        content=edition.pages[page_number],
        watermark=_watermark(identity, edition.book_id, edition.edition_id),
        expires_at=grant.expires_at.isoformat() if grant.expires_at else None,
    )


def protected_reader_headers() -> dict[str, str]:
    """Web deterrence only; NOT screenshot-proof or camera-proof protection."""
    return {
        "Cache-Control": "private, no-store, max-age=0",
        "Pragma": "no-cache",
        "Content-Security-Policy": (
            "default-src 'none'; frame-ancestors 'none'; base-uri 'none'; "
            "form-action 'none'"
        ),
        "Permissions-Policy": "display-capture=(), camera=(), microphone=()",
        "Referrer-Policy": "no-referrer",
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
    }
