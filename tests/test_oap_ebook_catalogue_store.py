"""Real schema must stay unapplied and catalogue reads fail closed."""

import uuid
from contextlib import contextmanager

import pytest

from mission_control import oap_ebook_catalogue_store as store
from mission_control.oap_ebook_reader import manuscript_digest

OWNER = str(uuid.UUID("6bf94814-e8b4-422d-b3b1-d69063ba491c"))
PAGES = ["first", "second"]
DIGEST = manuscript_digest(tuple(PAGES))
NAMES = (
    "book_id", "edition_id", "creator_id", "publisher_authority_id",
    "rights_record_id", "founder_approval_id", "rights_verified",
    "manuscript_approved", "public_release_approved", "status",
    "core_free", "premium", "private", "youth", "safeguarding_approved",
    "age_approved", "rights_allow_rotation", "rotation_rights_record_id",
    "owner_id", "manuscript_sha256", "pages_json", "preview_pages_json",
    "rights_expires_at",
)


def entry(**changes):
    values = dict.fromkeys(NAMES)
    values.update(
        book_id="food", edition_id="v1", creator_id="creator",
        publisher_authority_id="publisher", rights_record_id="rights",
        founder_approval_id="approval", rights_verified=True,
        manuscript_approved=True, public_release_approved=True,
        status="APPROVED", core_free=True, premium=False, private=False,
        youth=False, safeguarding_approved=False, age_approved=False,
        rights_allow_rotation=False, rotation_rights_record_id=None,
        owner_id=None, manuscript_sha256=DIGEST, pages_json=PAGES,
        preview_pages_json=[0], rights_expires_at=None,
    )
    values.update(changes)
    return tuple(values[name] for name in NAMES)


def attach(monkeypatch, row):
    observed = []

    class Cursor:
        def execute(self, sql, params):
            observed.append((sql, params))
            return self

        def fetchone(self):
            return row

    @contextmanager
    def connect(*, readonly=False):
        assert readonly is True
        yield Cursor()

    monkeypatch.setattr(store.postgres_db, "connect", connect)
    return observed


def lookup():
    return store.resolve_trusted_ebook("food", "v1")


def test_no_migration_or_public_content_on_import():
    result = store.catalogue_schema_plan()
    assert result["applied"] is False
    assert "DEFAULT 'DRAFT'" in result["statements"][0]
    assert "payment" not in result["statements"][0].lower()


def test_only_server_scoped_read_and_real_page_digest(monkeypatch):
    observed = attach(monkeypatch, entry())
    resolved = lookup()
    assert resolved is not None
    assert resolved.book.core_free
    assert resolved.manuscript.pages == tuple(PAGES)
    assert resolved.approval.rights_verified
    assert observed[0][1] == ("food", "v1")
    assert "WHERE book_id=%s AND edition_id=%s" in observed[0][0]


def test_missing_edition_is_not_invented(monkeypatch):
    attach(monkeypatch, None)
    assert lookup() is None


@pytest.mark.parametrize("changes", (
    {"status": "DRAFT"},
    {"status": "REVOKED"},
    {"manuscript_sha256": "a" * 64},
    {"pages_json": ["tampered", "second"]},
    {"preview_pages_json": [999]},
    {"preview_pages_json": [0, 0]},
    {"private": True, "owner_id": None},
    {"rights_allow_rotation": True, "rotation_rights_record_id": None},
))
def test_bad_or_unapproved_edition_is_unavailable(monkeypatch, changes):
    attach(monkeypatch, entry(**changes))
    with pytest.raises(store.EbookCatalogueUnavailable):
        lookup()


def test_private_owner_scope_preserved(monkeypatch):
    attach(monkeypatch, entry(
        private=True, core_free=False, owner_id=OWNER,
        public_release_approved=False,
    ))
    trusted = lookup()
    assert trusted is not None
    assert trusted.owner_id == OWNER
    assert trusted.approval.private is True


def test_unavailable_schema_fails_closed(monkeypatch):
    def broken(*, readonly=False):
        raise RuntimeError("missing table")

    monkeypatch.setattr(store.postgres_db, "connect", broken)
    with pytest.raises(store.EbookCatalogueUnavailable, match="catalogue_read_failed"):
        lookup()


def test_schema_is_not_executed(monkeypatch):
    attach(monkeypatch, entry())
    assert lookup() is not None


def test_bad_selector_is_rejected_before_database():
    with pytest.raises(ValueError):
        store.resolve_trusted_ebook("", "v1")
