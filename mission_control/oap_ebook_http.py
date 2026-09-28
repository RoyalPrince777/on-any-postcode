"""Isolated first-party ebook HTTP boundary, deliberately not registered live.

Trusted resolution must load verified rights, actual pages and owner information
from the SERVER. Request arguments provide only the book/edition/page selector;
never accept purchase claims, rights approvals or raw manuscript paths.
"""
from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone

from flask import Blueprint, jsonify, make_response, request

from . import web_security
from .oap_book_access import Book, Rotation
from .oap_book_entitlements import BookEntitlementsUnavailable
from .oap_book_publication import EditionEvidence
from .oap_ebook_reader import EbookEdition, protected_reader_headers
from .oap_ebook_service import read_ebook_page

_ID = re.compile(r"[a-zA-Z0-9][a-zA-Z0-9_-]{0,159}\Z")


@dataclass(frozen=True)
class TrustedEbook:
    book: Book
    approval: EditionEvidence
    manuscript: EbookEdition
    owner_id: str | None = None
    rotation: Rotation | None = None


def create_ebook_blueprint(
    resolve_trusted_ebook: Callable[[str, str], TrustedEbook | None],
) -> Blueprint:
    """Create an isolated reader; caller must separately verify readiness.

    This function does not register itself with the app, create a sample book,
    migrate tables, assume a signed licence or expose private files.
    """
    bp = Blueprint("oap_ebook_reader", __name__)

    @bp.get("/library/ebooks/<book_id>/<edition_id>/pages/<int:page_number>")
    def ebook_page(book_id: str, edition_id: str, page_number: int):
        def respond(payload: dict[str, object], status: int):
            response = make_response(jsonify(payload), status)
            response.headers.update(protected_reader_headers())
            return response

        if not _ID.fullmatch(book_id) or not _ID.fullmatch(edition_id):
            return respond({"error": "invalid_book_selector"}, 400)
        try:
            identity = web_security.current_authenticated_user()
            member_id = str(identity["id"]) if identity is not None else None
            trusted = resolve_trusted_ebook(book_id, edition_id)
            if trusted is None:
                return respond({"error": "book_unavailable"}, 404)
            excerpt_only = request.args.get("preview") == "1"
            page = read_ebook_page(
                book=trusted.book,
                approval=trusted.approval,
                manuscript=trusted.manuscript,
                authenticated_identity=member_id,
                private_owner_id=trusted.owner_id,
                rotation=trusted.rotation,
                now=datetime.now(timezone.utc),
                page_number=page_number,
                preview=excerpt_only,
            )
        except (PermissionError, ValueError, TypeError):
            return respond({"error": "book_unavailable"}, 404)
        except (BookEntitlementsUnavailable, OSError):
            return respond({"error": "reader_unavailable"}, 503)
        return respond(
            {
                "page": page.number,
                "content": page.content,
                "watermark": page.watermark,
                "expires_at": page.expires_at,
            },
            200,
        )

    return bp
