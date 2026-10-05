"""OAP Library creator draft workflow stays owner-scoped and fail-closed."""

import uuid
from contextlib import contextmanager
from datetime import datetime, timezone

import pytest

from mission_control import oap_ebook_creator_store as store

OWNER = str(uuid.UUID("6bf94814-e8b4-422d-b3b1-d69063ba491c"))


class FakeCursor:
    def __init__(self, row=None, rows=None):
        self.row = row
        self.rows = rows or []
        self.sql = ""
        self.parameters = None

    def execute(self, sql, parameters=None):
        self.sql = sql
        self.parameters = parameters
        return self

    def fetchone(self):
        return self.row

    def fetchall(self):
        return self.rows


def connect_with(monkeypatch, cursor):
    @contextmanager
    def connect(*, readonly=False):
        yield cursor
    monkeypatch.setattr(store.postgres_db, "connect", connect)


def test_create_draft_hashes_manuscript_and_stays_draft(monkeypatch):
    draft_id = str(uuid.uuid4())
    cursor = FakeCursor(row=(draft_id, "my-book", "v1", "My Book", "DRAFT", "a" * 64))
    connect_with(monkeypatch, cursor)

    result = store.create_draft(
        OWNER,
        book_id="my-book",
        edition_id="v1",
        title="My Book",
        pages=["Page one", "Page two"],
        price_minor=100,
    )

    assert result["state"] == "DRAFT"
    assert "INSERT INTO oap_ebook_creator_drafts" in cursor.sql
    assert cursor.parameters[1] == OWNER
    assert cursor.parameters[2] == "my-book"


def test_submit_requires_explicit_rights_attestation():
    with pytest.raises(PermissionError):
        store.submit_for_review(OWNER, str(uuid.uuid4()), rights_attested=False)


def test_submit_moves_only_owned_draft_to_review(monkeypatch):
    draft_id = str(uuid.uuid4())
    cursor = FakeCursor(row=(draft_id, "my-book", "v1", "My Book", "REVIEW_REQUIRED", "a" * 64))
    connect_with(monkeypatch, cursor)

    result = store.submit_for_review(OWNER, draft_id, rights_attested=True)

    assert result["state"] == "REVIEW_REQUIRED"
    assert result["publication_approved"] is False
    assert result["market_product_created"] is False
    assert result["payment_capture_performed"] is False
    assert cursor.parameters == (draft_id, OWNER)


def test_list_drafts_is_owner_scoped_and_read_only(monkeypatch):
    now = datetime(2026, 10, 5, tzinfo=timezone.utc)
    cursor = FakeCursor(rows=[(
        str(uuid.uuid4()), "my-book", "v1", "My Book", "", "en",
        100, "DRAFT", False, "a" * 64, now,
    )])
    observed = []

    @contextmanager
    def connect(*, readonly=False):
        observed.append(readonly)
        yield cursor

    monkeypatch.setattr(store.postgres_db, "connect", connect)
    drafts = store.list_drafts(OWNER)

    assert drafts[0]["book_id"] == "my-book"
    assert cursor.parameters == (OWNER,)
    assert observed == [True]
