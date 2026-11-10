"""Approved ebook Market bridge requires certification and approval evidence."""

import uuid
from contextlib import contextmanager

import pytest

from mission_control import oap_ebook_market as market

SELLER = str(uuid.UUID("6bf94814-e8b4-422d-b3b1-d69063ba491c"))
BUYER = str(uuid.UUID("11111111-1111-4111-8111-111111111111"))
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



def test_public_product_requires_active_approved_digital_listing(monkeypatch):
    connection = FakeConnection([(
        "book", "v1", PRODUCT, "ACTIVE", "My Book", "Digital description",
        750, "GBP", "OAP Seller", "creator-1", "publisher-1",
    )])
    wire(monkeypatch, connection)

    product = market.public_product("book", "v1")

    assert product is not None
    assert product["product_id"] == PRODUCT
    assert product["title"] == "My Book"
    assert product["physical_product"] is False
    assert product["payment_capture_performed"] is False
    sql = connection.calls[0][0]
    assert "m.state='ACTIVE'" in sql
    assert "e.public_release_approved IS TRUE" in sql


def test_public_product_hides_unavailable_listing(monkeypatch):
    connection = FakeConnection([None])
    wire(monkeypatch, connection)

    assert market.public_product("book", "v1") is None



def test_unlock_intent_is_digital_only_and_does_not_grant_ownership(monkeypatch):
    order_id = str(uuid.uuid4())
    intent_id = str(uuid.uuid4())
    connection = FakeConnection([
        (1,),
        (PRODUCT, SELLER, "My Book", 750, "GBP"),
        None,
        (order_id, "PAYMENT_PROVIDER_REQUIRED"),
        (intent_id, "PROVIDER_REQUIRED"),
    ])
    wire(monkeypatch, connection)

    result = market.create_unlock_intent(
        BUYER,
        book_id="book",
        edition_id="v1",
        idempotency_key="ebook-unlock-0001",
    )

    assert result["order_id"] == order_id
    assert result["payment_intent_id"] == intent_id
    assert result["order_state"] == "PAYMENT_PROVIDER_REQUIRED"
    assert result["payment_state"] == "PROVIDER_REQUIRED"
    assert result["payment_capture_performed"] is False
    assert result["provider_called"] is False
    assert result["fulfilment_intent_created"] is False
    assert result["entitlement_issued"] is False
    assert result["ownership_granted"] is False
    sql = "\n".join(call[0] for call in connection.calls)
    assert "INSERT INTO oap_commerce_orders" in sql
    assert "INSERT INTO oap_commerce_payment_intents" in sql
    assert "oap_commerce_fulfilment_intents" not in sql


def test_unlock_intent_rejects_unavailable_buyer(monkeypatch):
    connection = FakeConnection([None])
    wire(monkeypatch, connection)

    with pytest.raises(PermissionError, match="buyer_unavailable"):
        market.create_unlock_intent(
            BUYER,
            book_id="book",
            edition_id="v1",
            idempotency_key="ebook-unlock-0002",
        )
