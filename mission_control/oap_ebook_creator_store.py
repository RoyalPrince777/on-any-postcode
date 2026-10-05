"""Durable creator-side ebook drafts for OAP Library.

Creators may create and edit their own digital manuscript drafts and submit them
for review. This module never verifies rights, approves publication, creates a
Market product, captures payment, or grants an entitlement.
"""
from __future__ import annotations

import hashlib
import re
import uuid
from typing import Any

from . import postgres_db
from .oap_ebook_reader import manuscript_digest

MIGRATION_VERSION = "oap_ebook_creator_drafts_v1"
_SLUG = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,158}[a-z0-9])?$")

SCHEMA_STATEMENTS = (
    """CREATE TABLE IF NOT EXISTS oap_ebook_creator_drafts (
        draft_id UUID PRIMARY KEY,
        owner_identity_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
        book_id TEXT NOT NULL CHECK (char_length(book_id) BETWEEN 1 AND 160),
        edition_id TEXT NOT NULL CHECK (char_length(edition_id) BETWEEN 1 AND 160),
        title TEXT NOT NULL CHECK (char_length(title) BETWEEN 1 AND 200),
        description TEXT NOT NULL DEFAULT '' CHECK (char_length(description) <= 2000),
        language TEXT NOT NULL DEFAULT 'en' CHECK (char_length(language) BETWEEN 2 AND 32),
        price_minor BIGINT CHECK (price_minor IS NULL OR price_minor >= 0),
        pages_json JSONB NOT NULL CHECK (jsonb_typeof(pages_json)='array'),
        manuscript_sha256 CHAR(64) NOT NULL,
        rights_attested BOOLEAN NOT NULL DEFAULT FALSE,
        state TEXT NOT NULL DEFAULT 'DRAFT'
            CHECK (state IN ('DRAFT','REVIEW_REQUIRED','APPROVED','REJECTED','ARCHIVED')),
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(owner_identity_id,book_id,edition_id)
    )""",
    """CREATE INDEX IF NOT EXISTS ix_ebook_creator_owner_updated
       ON oap_ebook_creator_drafts(owner_identity_id,updated_at DESC)""",
)
MIGRATION_CHECKSUM = hashlib.sha256("\n".join(SCHEMA_STATEMENTS).encode()).hexdigest()


class EbookCreatorStoreUnavailable(RuntimeError):
    pass


def init_schema(*, assume_yes: bool = False, dry_run: bool = False) -> dict[str, object]:
    if not assume_yes:
        raise RuntimeError("explicit_confirmation_required")
    if dry_run:
        return {
            "migration": MIGRATION_VERSION,
            "checksum": MIGRATION_CHECKSUM,
            "schema_ready": False,
            "dry_run": True,
        }
    try:
        with postgres_db.connect() as connection:
            for statement in SCHEMA_STATEMENTS:
                connection.execute(statement)
            connection.commit()
    except Exception as exc:
        raise EbookCreatorStoreUnavailable("ebook_creator_schema_init_failed") from exc
    return {
        "migration": MIGRATION_VERSION,
        "checksum": MIGRATION_CHECKSUM,
        "schema_ready": True,
        "dry_run": False,
    }


def _identity(value: object) -> str:
    try:
        return str(uuid.UUID(str(value)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError("invalid_owner_identity") from exc


def _slug(value: object, field: str) -> str:
    text = str(value or "").strip().lower()
    if not _SLUG.fullmatch(text):
        raise ValueError(f"invalid_{field}")
    return text


def _pages(value: object) -> tuple[str, ...]:
    if not isinstance(value, list) or not 1 <= len(value) <= 10000:
        raise ValueError("invalid_pages")
    pages = tuple(str(page) for page in value)
    if any(not page.strip() or len(page) > 12000 for page in pages):
        raise ValueError("invalid_pages")
    return pages


def create_draft(
    owner_identity_id: object,
    *,
    book_id: object,
    edition_id: object,
    title: object,
    description: object = "",
    language: object = "en",
    price_minor: object = None,
    pages: object,
) -> dict[str, Any]:
    owner = _identity(owner_identity_id)
    book = _slug(book_id, "book_id")
    edition = _slug(edition_id, "edition_id")
    title_value = str(title or "").strip()
    description_value = str(description or "").strip()
    language_value = str(language or "en").strip().lower()
    if not 1 <= len(title_value) <= 200:
        raise ValueError("invalid_title")
    if len(description_value) > 2000 or not 2 <= len(language_value) <= 32:
        raise ValueError("invalid_description_or_language")
    page_values = _pages(pages)
    price = None if price_minor in (None, "") else int(price_minor)
    if price is not None and price < 0:
        raise ValueError("invalid_price")
    digest = manuscript_digest(page_values)
    draft_id = str(uuid.uuid4())
    try:
        with postgres_db.connect() as connection:
            row = connection.execute(
                """INSERT INTO oap_ebook_creator_drafts(
                       draft_id,owner_identity_id,book_id,edition_id,title,description,
                       language,price_minor,pages_json,manuscript_sha256,state)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s,'DRAFT')
                   RETURNING draft_id,book_id,edition_id,title,state,manuscript_sha256""",
                (
                    draft_id, owner, book, edition, title_value, description_value,
                    language_value, price, __import__("json").dumps(page_values), digest,
                ),
            ).fetchone()
            connection.commit()
    except Exception as exc:
        raise EbookCreatorStoreUnavailable("ebook_draft_create_failed") from exc
    return {
        "draft_id": str(row[0]), "book_id": str(row[1]), "edition_id": str(row[2]),
        "title": str(row[3]), "state": str(row[4]), "manuscript_sha256": str(row[5]),
    }


def list_drafts(owner_identity_id: object) -> tuple[dict[str, Any], ...]:
    owner = _identity(owner_identity_id)
    try:
        with postgres_db.connect(readonly=True) as connection:
            rows = connection.execute(
                """SELECT draft_id,book_id,edition_id,title,description,language,
                          price_minor,state,rights_attested,manuscript_sha256,updated_at
                   FROM oap_ebook_creator_drafts
                   WHERE owner_identity_id=%s ORDER BY updated_at DESC""",
                (owner,),
            ).fetchall()
    except Exception as exc:
        raise EbookCreatorStoreUnavailable("ebook_draft_list_failed") from exc
    return tuple(
        {
            "draft_id": str(r[0]), "book_id": str(r[1]), "edition_id": str(r[2]),
            "title": str(r[3]), "description": str(r[4]), "language": str(r[5]),
            "price_minor": None if r[6] is None else int(r[6]), "state": str(r[7]),
            "rights_attested": bool(r[8]), "manuscript_sha256": str(r[9]),
            "updated_at": r[10].isoformat(),
        } for r in rows
    )


def submit_for_review(owner_identity_id: object, draft_id: object, *, rights_attested: object) -> dict[str, Any]:
    owner = _identity(owner_identity_id)
    try:
        draft = str(uuid.UUID(str(draft_id)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError("invalid_draft_id") from exc
    if rights_attested is not True:
        raise PermissionError("rights_attestation_required")
    try:
        with postgres_db.connect() as connection:
            row = connection.execute(
                """UPDATE oap_ebook_creator_drafts
                   SET rights_attested=TRUE,state='REVIEW_REQUIRED',
                       updated_at=CURRENT_TIMESTAMP
                   WHERE draft_id=%s AND owner_identity_id=%s AND state='DRAFT'
                   RETURNING draft_id,book_id,edition_id,title,state,manuscript_sha256""",
                (draft, owner),
            ).fetchone()
            if row is None:
                raise PermissionError("draft_not_owned_or_not_editable")
            connection.commit()
    except PermissionError:
        raise
    except Exception as exc:
        raise EbookCreatorStoreUnavailable("ebook_draft_submit_failed") from exc
    return {
        "draft_id": str(row[0]), "book_id": str(row[1]), "edition_id": str(row[2]),
        "title": str(row[3]), "state": str(row[4]), "manuscript_sha256": str(row[5]),
        "publication_approved": False,
        "market_product_created": False,
        "payment_capture_performed": False,
    }
