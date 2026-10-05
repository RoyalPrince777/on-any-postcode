"""Approved ebook Market bridge requires certification and approval evidence."""

import uuid
from contextlib import contextmanager

import pytest

from mission_control import oap_ebook_market as market

SELLER = str(uuid.UUID("6bf94814-e8b4-422d-b3b1-d69063ba491c"))
PRODUCT = str(uuid.UUID("5d0af9ce-a6df-40f7-b837-36fbeaa71cf1"))


class FakeConnection:
    def __init__(self, rows):
        self.rows = list(rows)
        self.calls = []
        self.committed = False

    def execute(self, sql, parameters=None):
        self.calls.append((sql, parameters))
        return self

    def fetchone(self):
        return self.rows.pop(0) if self.rows else None

    def commit(self):
        self.committed = True


def wire(monkeypatch, connection):
    @contextmanager
    def connect(*, readonly=False):
        yield connection
    monkeypatch.setattr(market.postgres_db, "connect", connect)


def test_publish_requires_certified_merchant(monkeypatch):
    connection = FakeConnection([None])
    wire(monkeypatch, connection)

    with pytest.raises(PermissionError, match="certified_merchant_required"):
        market.publish_approved_ebook(SELLER, book_id="book", edition_id="v1")


def test_publish_requires_approved_matching_digital_evidence(monkeypatch):
    connection = FakeConnection([(1,), None, None])
    wire(monkeypatch, connection)

    with pytest.raises(PermissionError, match="ebook_not_approved_for_market"):
        market.publish_approved_ebook(SELLER, book_id="book", edition_id="v1")


def test_publish_creates_product_without_payment_or_entitlement(monkeypatch):
    connection = FakeConnection([
        (1,),
        None,
        ("My Book", "Digital description", 750, "a" * 64),
        (PRODUCT,),
        None,
    ])
    wire(monkeypatch, connection)

    result = market.publish_approved_ebook(
        SELLER, book_id="book", edition_id="v1"
    )

    assert result["product_id"] == PRODUCT
    assert result["state"] == "ACTIVE"
    assert result["created"] is True
    assert result["payment_capture_performed"] is False
    assert result["entitlement_issued"] is False
    assert connection.committed is True
    joined_sql = "\n".join(call[0] for call in connection.calls)
    assert "role_id='certified_merchant'" in joined_sql
    assert "d.state='APPROVED'" in joined_sql
    assert "e.rights_verified IS TRUE" in joined_sql
    assert "e.public_release_approved IS TRUE" in joined_sql


def test_existing_market_link_is_idempotent(monkeypatch):
    connection = FakeConnection([(1,), (PRODUCT, "ACTIVE")])
    wire(monkeypatch, connection)

    result = market.publish_approved_ebook(
        SELLER, book_id="book", edition_id="v1"
    )

    assert result["product_id"] == PRODUCT
    assert result["created"] is False
    assert result["payment_capture_performed"] is False
