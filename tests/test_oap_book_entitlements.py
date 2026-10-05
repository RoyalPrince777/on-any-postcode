"""Entitlement lookup is owner scoped, read-only and fails closed."""

import uuid
from contextlib import contextmanager

import pytest

from mission_control import oap_book_entitlements as entitlements

OWNER = str(uuid.UUID("6bf94814-e8b4-422d-b3b1-d69063ba491c"))


class FakeConnection:
    def __init__(self, row):
        self.row = row
        self.parameters = None
        self.sql = ""

    def execute(self, sql, parameters):
        self.sql = sql
        self.parameters = parameters
        return self

    def fetchone(self):
        return self.row


def store(monkeypatch, row):
    connection = FakeConnection(row)
    observed = []

    @contextmanager
    def connect(*, readonly=False):
        observed.append(readonly)
        yield connection

    monkeypatch.setattr(entitlements.postgres_db, "connect", connect)
    return connection, observed


def test_schema_is_plan_only():
    plan = entitlements.schema_plan()
    assert plan["applied"] is False
    assert "identity_id" in plan["statements"][0]
    assert "payment_verified" in plan["statements"][0]
    assert "UNIQUE" in plan["statements"][0]


def test_verified_purchase_is_read_only_and_scoped(monkeypatch):
    connection, observed = store(monkeypatch, ("receipt-1",))
    receipt = entitlements.lookup_verified_purchase(
        authenticated_identity_id=OWNER, book_id="book", edition_id="v1"
    )
    assert receipt is not None
    assert receipt.owner_id == OWNER
    assert receipt.payment_verified is True
    assert receipt.payment_receipt_id == "receipt-1"
    assert connection.parameters == (OWNER, "book", "v1")
    assert "payment_verified IS TRUE" in connection.sql
    assert "revoked IS FALSE" in connection.sql
    assert observed == [True]


def test_missing_entitlement_denied_without_inventing_receipt(monkeypatch):
    store(monkeypatch, None)
    assert entitlements.lookup_verified_purchase(
        authenticated_identity_id=OWNER, book_id="book", edition_id="v1"
    ) is None


@pytest.mark.parametrize(("identity", "book", "edition"), (
    ("not-a-uuid", "book", "v1"),
    (OWNER, "", "v1"),
    (OWNER, "book", ""),
))
def test_invalid_identity_or_scope_rejected(identity, book, edition):
    with pytest.raises(ValueError):
        entitlements.lookup_verified_purchase(
            authenticated_identity_id=identity, book_id=book, edition_id=edition
        )


def test_unavailable_store_fails_closed(monkeypatch):
    def broken(*, readonly=False):
        raise RuntimeError("offline")

    monkeypatch.setattr(entitlements.postgres_db, "connect", broken)
    with pytest.raises(entitlements.BookEntitlementsUnavailable):
        entitlements.lookup_verified_purchase(
            authenticated_identity_id=OWNER, book_id="book", edition_id="v1"
        )


def test_empty_receipt_is_rejected(monkeypatch):
    store(monkeypatch, ("",))
    with pytest.raises(entitlements.BookEntitlementsUnavailable):
        entitlements.lookup_verified_purchase(
            authenticated_identity_id=OWNER, book_id="book", edition_id="v1"
        )
