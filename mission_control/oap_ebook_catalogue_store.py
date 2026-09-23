"""Unapplied first-party ebook catalogue and manuscript storage contract.

Creation/publishing is intentionally out of scope: every row must be populated
through a separately governed rights review and content approval workflow.
This read-only resolver never grants a licence, creates a sample manuscript,
migrates a database, calls an external provider or makes files public.
"""
from __future__ import annotations

import json
import uuid
from collections.abc import Mapping

from . import postgres_db
from .oap_book_access import Book
from .oap_book_publication import EditionEvidence
from .oap_ebook_http import TrustedEbook
from .oap_ebook_reader import EbookEdition, manuscript_digest

CATALOGUE_SCHEMA_VERSION = "oap_ebook_catalogue_v1"
CATALOGUE_SCHEMA_SQL = (
    """CREATE TABLE IF NOT EXISTS oap_ebook_editions (
        book_id TEXT NOT NULL CHECK (char_length(book_id) BETWEEN 1 AND 160),
        edition_id TEXT NOT NULL CHECK (char_length(edition_id) BETWEEN 1 AND 160),
        creator_id TEXT NOT NULL,
        publisher_authority_id TEXT NOT NULL,
        rights_record_id TEXT NOT NULL,
        founder_approval_id TEXT NOT NULL,
        rights_verified BOOLEAN NOT NULL DEFAULT FALSE,
        manuscript_approved BOOLEAN NOT NULL DEFAULT FALSE,
        public_release_approved BOOLEAN NOT NULL DEFAULT FALSE,
        status TEXT NOT NULL DEFAULT 'DRAFT'
            CHECK (status IN ('DRAFT','REVIEW','APPROVED','REVOKED')),
        core_free BOOLEAN NOT NULL DEFAULT FALSE,
        premium BOOLEAN NOT NULL DEFAULT FALSE,
        private BOOLEAN NOT NULL DEFAULT TRUE,
        youth BOOLEAN NOT NULL DEFAULT FALSE,
        safeguarding_approved BOOLEAN NOT NULL DEFAULT FALSE,
        age_approved BOOLEAN NOT NULL DEFAULT FALSE,
        rights_allow_rotation BOOLEAN NOT NULL DEFAULT FALSE,
        rotation_rights_record_id TEXT,
        owner_id UUID REFERENCES users(id) ON DELETE RESTRICT,
        manuscript_sha256 CHAR(64) NOT NULL,
        pages_json JSONB NOT NULL
            CHECK (jsonb_typeof(pages_json) = 'array'),
        preview_pages_json JSONB NOT NULL DEFAULT '[]'::jsonb
            CHECK (jsonb_typeof(preview_pages_json) = 'array'),
        rights_expires_at TIMESTAMPTZ,
        PRIMARY KEY (book_id,edition_id),
        CHECK (NOT (core_free AND premium)),
        CHECK (NOT (private AND core_free)),
        CHECK (NOT private OR owner_id IS NOT NULL),
        CHECK (NOT rights_allow_rotation
               OR rotation_rights_record_id IS NOT NULL)
    )""",
)


class EbookCatalogueUnavailable(RuntimeError):
    """Trusted catalogue was not available or did not satisfy its contract."""


def catalogue_schema_plan() -> dict[str, object]:
    return {
        "version": CATALOGUE_SCHEMA_VERSION,
        "statements": CATALOGUE_SCHEMA_SQL,
        "applied": False,
    }


def _json_array(value: object) -> list[object]:
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError as exc:
            raise EbookCatalogueUnavailable("catalogue_invalid_json") from exc
    if not isinstance(value, list):
        raise EbookCatalogueUnavailable("catalogue_invalid_array")
    return value


def _record_from_row(row: Mapping[str, object]) -> TrustedEbook:
    """Require a concrete database-mapped approved edition, not request flags."""
    if row["status"] != "APPROVED":
        raise EbookCatalogueUnavailable("catalogue_not_approved")
    pages = _json_array(row["pages_json"])
    previews = _json_array(row["preview_pages_json"])
    if (
        not pages or len(pages) > 10000
        or any(not isinstance(p, str) or not 0 < len(p) <= 12000 for p in pages)
        or any(type(i) is not int or not 0 <= i < len(pages) for i in previews)
        or len(set(previews)) != len(previews)
    ):
        raise EbookCatalogueUnavailable("catalogue_invalid_pages")
    digest = str(row["manuscript_sha256"])
    if manuscript_digest(tuple(pages)) != digest:
        raise EbookCatalogueUnavailable("catalogue_manuscript_mismatch")
    book_id = str(row["book_id"])
    edition_id = str(row["edition_id"])
    private = row["private"] is True
    owner = row["owner_id"]
    if private:
        try:
            owner = str(uuid.UUID(str(owner)))
        except (TypeError, ValueError, AttributeError) as exc:
            raise EbookCatalogueUnavailable("catalogue_invalid_owner") from exc
    if row["rights_allow_rotation"] is True and not row["rotation_rights_record_id"]:
        raise EbookCatalogueUnavailable("catalogue_rotation_rights_missing")
    book = Book(
        book_id=book_id, core_free=row["core_free"] is True,
        premium=row["premium"] is True, private=private,
        youth=row["youth"] is True,
        rights_evidence=str(row["rotation_rights_record_id"] or "") or None,
        rights_allow_rotation=row["rights_allow_rotation"] is True,
        safeguarding_approved=row["safeguarding_approved"] is True,
        age_approved=row["age_approved"] is True,
    )
    approval = EditionEvidence(
        book_id=book_id, edition_id=edition_id, manuscript_sha256=digest,
        creator_id=str(row["creator_id"]), publisher_authority_id=str(
            row["publisher_authority_id"]
        ), rights_record_id=str(row["rights_record_id"]),
        founder_approval_id=str(row["founder_approval_id"]),
        rights_verified=row["rights_verified"] is True,
        manuscript_approved=row["manuscript_approved"] is True,
        public_release_approved=row["public_release_approved"] is True,
        private=private, youth=row["youth"] is True,
        safeguarding_approved=row["safeguarding_approved"] is True,
        age_approved=row["age_approved"] is True,
        expires_at=row["rights_expires_at"],
    )
    manuscript = EbookEdition(
        book_id, edition_id, digest, tuple(pages), frozenset(previews)
    )
    return TrustedEbook(book, approval, manuscript, owner_id=owner)


def resolve_trusted_ebook(book_id: str, edition_id: str) -> TrustedEbook | None:
    """Read a governed edition; unavailable schema and corruption fail closed."""
    if not (
        isinstance(book_id, str) and isinstance(edition_id, str)
        and 0 < len(book_id) <= 160 and 0 < len(edition_id) <= 160
    ):
        raise ValueError("invalid_ebook_selector")
    try:
        with postgres_db.connect(readonly=True) as connection:
            cursor = connection.execute(
                """SELECT book_id,edition_id,creator_id,publisher_authority_id,
                          rights_record_id,founder_approval_id,rights_verified,
                          manuscript_approved,public_release_approved,status,
                          core_free,premium,private,youth,safeguarding_approved,
                          age_approved,rights_allow_rotation,
                          rotation_rights_record_id,owner_id,manuscript_sha256,
                          pages_json,preview_pages_json,rights_expires_at
                   FROM oap_ebook_editions WHERE book_id=%s AND edition_id=%s""",
                (book_id, edition_id),
            )
            row = cursor.fetchone()
    except Exception as exc:
        raise EbookCatalogueUnavailable("catalogue_read_failed") from exc
    if row is None:
        return None
    names = (
        "book_id", "edition_id", "creator_id", "publisher_authority_id",
        "rights_record_id", "founder_approval_id", "rights_verified",
        "manuscript_approved", "public_release_approved", "status",
        "core_free", "premium", "private", "youth", "safeguarding_approved",
        "age_approved", "rights_allow_rotation", "rotation_rights_record_id",
        "owner_id", "manuscript_sha256", "pages_json", "preview_pages_json",
        "rights_expires_at",
    )
    if len(row) != len(names):
        raise EbookCatalogueUnavailable("catalogue_invalid_record")
    try:
        return _record_from_row(dict(zip(names, row, strict=True)))
    except (KeyError, TypeError, ValueError, AttributeError) as exc:
        raise EbookCatalogueUnavailable("catalogue_invalid_record") from exc
