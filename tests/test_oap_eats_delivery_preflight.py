"""Regression coverage for Eats customer-only delivery preflight."""
from datetime import UTC, datetime
from unittest.mock import Mock

import pytest

from mission_control import oap_eats_fulfilment, oap_eats_store

CUSTOMER = "11111111-1111-4111-8111-111111111111"
MERCHANT = "22222222-2222-4222-8222-222222222222"
ORDER = "33333333-3333-4333-8333-333333333333"
WHEN = datetime(2026, 10, 18, tzinfo=UTC)


class _Connection:
    def __init__(self, row):
        self.row = row
        self.sql = []

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def execute(self, sql, params=()):
        self.sql.append((sql, params))
        return self

    def fetchone(self):
        return self.row


def test_customer_preflight_rejects_non_customer(monkeypatch):
    connection = _Connection(None)
    monkeypatch.setattr(oap_eats_store.postgres_db, "connect", lambda **_: connection)
    with pytest.raises(PermissionError, match="order_customer_required"):
        oap_eats_store.STORE.require_customer_order(
            order_id=ORDER, customer_identity_id=MERCHANT
        )
    assert "customer_identity_id=%s" in connection.sql[0][0]
    assert connection.sql[0][1] == (ORDER, MERCHANT)


def test_customer_preflight_returns_owned_order(monkeypatch):
    row = (ORDER, MERCHANT, "authorised", 1599, "GBP", "delivery", None, None, None, WHEN, WHEN)
    connection = _Connection(row)
    monkeypatch.setattr(oap_eats_store.postgres_db, "connect", lambda **_: connection)
    order = oap_eats_store.STORE.require_customer_order(
        order_id=ORDER, customer_identity_id=CUSTOMER
    )
    assert order["order_id"] == ORDER
    assert order["fulfilment_mode"] == "delivery"


def test_delivery_denied_before_movement_booking(monkeypatch):
    movement = Mock()
    monkeypatch.setattr(oap_eats_fulfilment.movement_operations.STORE, "create_booking", movement)
    def deny(**_):
        raise PermissionError("order_customer_required")
    monkeypatch.setattr(oap_eats_fulfilment.oap_eats_store.STORE, "require_customer_order", deny)
    with pytest.raises(PermissionError, match="order_customer_required"):
        oap_eats_fulfilment.create_delivery(
            order_id=ORDER, customer_identity_id=MERCHANT,
            pickup={"label": "A"}, destination={"label": "B"},
            idempotency_key="eats-delivery-0001",
        )
    movement.assert_not_called()
