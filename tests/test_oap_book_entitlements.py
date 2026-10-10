"""Entitlement lookup is owner scoped, read-only and fails closed."""

import uuid
from contextlib import contextmanager
from datetime import UTC, datetime

import pytest

from mission_control import oap_book_entitlements as entitlements

OWNER = str(uuid.UUID("6bf94814-e8b4-422d-b3b1-d69063ba491c"))


class FakeConnection:
    def __init__(self, row):
        self.row = row
        self.parameters = None
        self.sql = ""
        self.calls = []
        self.committed = False

    def execute(self, sql, parameters):
        self.sql = sql
        self.parameters = parameters
        self.calls.append((sql, parameters))
        return self

    def fetchone(self):
        if isinstance(self.row, list):
            return self.row.pop(0) if self.row else None
        return self.row

    def fetchall(self):
        return self.row if isinstance(self.row, list) else ([] if self.row is None else [self.row])

    def commit(self):
        self.committed = True


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



def test_verified_purchase_library_only_returns_owned_approved_rows(monkeypatch):
    created = datetime(2026, 10, 5, tzinfo=UTC)
    row = (
        str(uuid.uuid4()), "book", "v1", "provider-receipt",
        "verification-receipt", created, "creator-1", "publisher-1", "a" * 64,
    )
    connection, observed = store(monkeypatch, [row])

    books = entitlements.list_verified_purchases(
        authenticated_identity_id=OWNER
    )

    assert len(books) == 1
    assert books[0]["book_id"] == "book"
    assert books[0]["edition_id"] == "v1"
    assert books[0]["state"] == "OWNED"
    assert connection.parameters == (OWNER,)
    assert "payment_verified IS TRUE" in connection.sql
    assert "revoked IS FALSE" in connection.sql
    assert "public_release_approved IS TRUE" in connection.sql
    assert observed == [True]


def test_verified_purchase_library_fails_closed_when_store_unavailable(monkeypatch):
    def broken(*, readonly=False):
        raise RuntimeError("offline")

    monkeypatch.setattr(entitlements.postgres_db, "connect", broken)
    with pytest.raises(entitlements.BookEntitlementsUnavailable):
        entitlements.list_verified_purchases(authenticated_identity_id=OWNER)



def test_verified_capture_mints_owned_entitlement(monkeypatch):
    order_id = str(uuid.uuid4())
    intent_id = str(uuid.uuid4())
    receipt_id = str(uuid.uuid4())
    entitlement_id = str(uuid.uuid4())
    connection = FakeConnection([
        (
            OWNER, "GBP", 750, str(uuid.uuid4()), 1, 750,
            intent_id, "CAPTURED", "provider-ref-1",
            "book", "v1", "ACTIVE",
            "APPROVED", False, True, True, True,
            receipt_id, "CAPTURED", "provider-ref-1",
        ),
        None,
        (entitlement_id, False, True),
    ])
    observed = []

    @contextmanager
    def connect(*, readonly=False):
        observed.append(readonly)
        yield connection

    monkeypatch.setattr(entitlements.postgres_db, "connect", connect)

    result = entitlements.grant_from_verified_capture(
        authenticated_identity_id=OWNER,
        order_id=order_id,
    )

    assert result["state"] == "OWNED"
    assert result["created"] is True
    assert result["payment_verified"] is True
    assert result["payment_capture_performed_here"] is False
    assert result["provider_called_here"] is False
    assert observed == [False]
    assert connection.committed is True
    joined_sql = "\n".join(sql for sql, _params in connection.calls)
    assert "oap_commerce_provider_receipts" in joined_sql
    assert "INSERT INTO oap_book_entitlements" in joined_sql


def test_verified_capture_rejects_non_captured_payment(monkeypatch):
    order_id = str(uuid.uuid4())
    connection = FakeConnection([
        (
            OWNER, "GBP", 750, str(uuid.uuid4()), 1, 750,
            str(uuid.uuid4()), "AUTHORIZED", "provider-ref-1",
            "book", "v1", "ACTIVE",
            "APPROVED", False, True, True, True,
            str(uuid.uuid4()), "CAPTURED", "provider-ref-1",
        )
    ])
    @contextmanager
    def connect(*, readonly=False):
        yield connection

    monkeypatch.setattr(entitlements.postgres_db, "connect", connect)
    with pytest.raises(PermissionError, match="payment_not_captured"):
        entitlements.grant_from_verified_capture(
            authenticated_identity_id=OWNER,
            order_id=order_id,
        )


def test_verified_capture_rejects_provider_reference_mismatch(monkeypatch):
    order_id = str(uuid.uuid4())
    connection = FakeConnection([
        (
            OWNER, "GBP", 750, str(uuid.uuid4()), 1, 750,
            str(uuid.uuid4()), "CAPTURED", "provider-ref-1",
            "book", "v1", "ACTIVE",
            "APPROVED", False, True, True, True,
            str(uuid.uuid4()), "CAPTURED", "provider-ref-2",
        )
    ])
    @contextmanager
    def connect(*, readonly=False):
        yield connection

    monkeypatch.setattr(entitlements.postgres_db, "connect", connect)
    with pytest.raises(PermissionError, match="provider_reference_mismatch"):
        entitlements.grant_from_verified_capture(
            authenticated_identity_id=OWNER,
            order_id=order_id,
        )



def test_verified_refund_revokes_owned_ebook(monkeypatch):
    order_id = str(uuid.uuid4())
    entitlement_id = str(uuid.uuid4())
    refund_receipt_id = str(uuid.uuid4())
    connection = FakeConnection([
        (
            entitlement_id, "book", "v1", False,
            "payment-intent-1", "CAPTURED", "capture-ref-1",
            refund_receipt_id, "REFUNDED", "refund-ref-1",
        ),
        (entitlement_id, True, True),
    ])

    @contextmanager
    def connect(*, readonly=False):
        yield connection

    monkeypatch.setattr(entitlements.postgres_db, "connect", connect)

    result = entitlements.reconcile_verified_refund(
        authenticated_identity_id=OWNER,
        order_id=order_id,
    )

    assert result["state"] == "REFUNDED"
    assert result["revoked"] is True
    assert result["refund_executed_here"] is False
    assert result["provider_called_here"] is False
    assert connection.committed is True


def test_verified_refund_reversal_restores_only_captured_payment(monkeypatch):
    order_id = str(uuid.uuid4())
    entitlement_id = str(uuid.uuid4())
    connection = FakeConnection([
        (
            entitlement_id, "book", "v1", True,
            "payment-intent-1", "CAPTURED", "capture-ref-1",
            str(uuid.uuid4()), "REVERSED", "refund-ref-1",
        ),
        (entitlement_id, False, True),
    ])

    @contextmanager
    def connect(*, readonly=False):
        yield connection

    monkeypatch.setattr(entitlements.postgres_db, "connect", connect)

    result = entitlements.reconcile_verified_refund(
        authenticated_identity_id=OWNER,
        order_id=order_id,
    )

    assert result["state"] == "OWNED"
    assert result["revoked"] is False


def test_refund_reversal_without_captured_payment_fails_closed(monkeypatch):
    order_id = str(uuid.uuid4())
    connection = FakeConnection([
        (
            str(uuid.uuid4()), "book", "v1", True,
            "payment-intent-1", "AUTHORIZED", "",
            str(uuid.uuid4()), "REVERSED", "refund-ref-1",
        )
    ])

    @contextmanager
    def connect(*, readonly=False):
        yield connection

    monkeypatch.setattr(entitlements.postgres_db, "connect", connect)

    with pytest.raises(PermissionError, match="refund_restore_capture_not_verified"):
        entitlements.reconcile_verified_refund(
            authenticated_identity_id=OWNER,
            order_id=order_id,
        )
