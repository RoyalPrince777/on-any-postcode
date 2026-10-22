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

    def commit(self):
        pass


@pytest.fixture(autouse=True)
def _unit_transaction(monkeypatch):
    connection = _Connection(None)
    monkeypatch.setattr(oap_eats_fulfilment.postgres_db, "connect", lambda **_: connection)


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


def test_delivery_retry_reuses_movement_booking_after_binding_failure(monkeypatch):
    """Same-key retry reuses the Movement booking after a transient Eats bind failure."""
    from unittest.mock import Mock

    order = {"fulfilment_mode": "delivery", "state": "authorised"}
    monkeypatch.setattr(
        oap_eats_fulfilment.oap_eats_store.STORE, "require_customer_order",
        lambda **_: order,
    )
    bookings = {}
    def create_booking(**kwargs):
        key = kwargs["idempotency_key"]
        if key in bookings and bookings[key]["payload"] != kwargs:
            raise ValueError("idempotency_conflict")
        if key not in bookings:
            bookings[key] = {"payload": kwargs, "booking_id": "44444444-4444-4444-8444-444444444444"}
        return {"booking_id": bookings[key]["booking_id"]}
    monkeypatch.setattr(oap_eats_fulfilment.movement_operations.STORE, "create_booking", create_booking)
    bind = Mock(side_effect=[RuntimeError("temporary_eats_store_failure"), {"movement_booking_id": "44444444-4444-4444-8444-444444444444"}])
    monkeypatch.setattr(oap_eats_fulfilment.oap_eats_store.STORE, "bind_movement", bind)
    args = {"order_id": ORDER, "customer_identity_id": CUSTOMER,
            "pickup": {"label": "A"}, "destination": {"label": "B"},
            "idempotency_key": "eats-delivery-retry-0001"}
    with pytest.raises(RuntimeError, match="temporary_eats_store_failure"):
        oap_eats_fulfilment.create_delivery(**args)
    result = oap_eats_fulfilment.create_delivery(**args)
    assert result["movement_booking_id"] == bookings[args["idempotency_key"]]["booking_id"]
    assert len(bookings) == 1
    assert bind.call_count == 2
    assert result["courier_dispatched"] is False
    assert result["external_dispatch_enabled"] is False


def test_delivery_retry_changed_payload_rejected_before_binding(monkeypatch):
    """A changed retry payload cannot silently reuse a Movement idempotency key."""
    from unittest.mock import Mock

    monkeypatch.setattr(
        oap_eats_fulfilment.oap_eats_store.STORE, "require_customer_order",
        lambda **_: {"fulfilment_mode": "delivery", "state": "authorised"},
    )
    seen = {}
    def create_booking(**kwargs):
        key = kwargs["idempotency_key"]
        if key in seen and kwargs != seen[key]:
            raise ValueError("idempotency_conflict")
        seen[key] = kwargs
        return {"booking_id": "44444444-4444-4444-8444-444444444444"}
    monkeypatch.setattr(oap_eats_fulfilment.movement_operations.STORE, "create_booking", create_booking)
    bind = Mock(return_value={"movement_booking_id": "44444444-4444-4444-8444-444444444444"})
    monkeypatch.setattr(oap_eats_fulfilment.oap_eats_store.STORE, "bind_movement", bind)
    args = {"order_id": ORDER, "customer_identity_id": CUSTOMER,
            "pickup": {"label": "A"}, "destination": {"label": "B"},
            "idempotency_key": "eats-delivery-retry-0002"}
    oap_eats_fulfilment.create_delivery(**args)
    with pytest.raises(ValueError, match="idempotency_conflict"):
        oap_eats_fulfilment.create_delivery(**{**args, "destination": {"label": "C"}})
    assert bind.call_count == 1
