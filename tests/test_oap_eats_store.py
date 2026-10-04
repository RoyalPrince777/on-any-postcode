from datetime import UTC, datetime

import pytest

from mission_control import oap_eats_store

CUSTOMER = "11111111-1111-4111-8111-111111111111"
MERCHANT = "22222222-2222-4222-8222-222222222222"
ORDER = "33333333-3333-4333-8333-333333333333"
WHEN = datetime(2026, 10, 4, tzinfo=UTC)


class _Result:
    def __init__(self, value):
        self.value = value
    def fetchone(self):
        return self.value


class _Connection:
    def __init__(self, insert_row):
        self.insert_row = insert_row
        self.sql = []
        self.committed = False
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False
    def commit(self):
        self.committed = True
    def execute(self, sql, params=()):
        self.sql.append((sql, params))
        if "SELECT 1 FROM oap_eats_merchants" in sql:
            return _Result((1,))
        if "INSERT INTO oap_eats_orders" in sql:
            return _Result(self.insert_row)
        if "INSERT INTO oap_eats_order_events" in sql:
            return _Result(None)
        raise AssertionError(sql)


def test_eats_order_idempotency_binds_immutable_payload(monkeypatch):
    row = (ORDER, MERCHANT, "created", 1599, "GBP", "delivery", None, None, None, WHEN, WHEN)
    connection = _Connection(row)
    monkeypatch.setattr(oap_eats_store.postgres_db, "connect", lambda **_: connection)
    result = oap_eats_store.STORE.create_order(
        customer_identity_id=CUSTOMER,
        merchant_id=MERCHANT,
        items=[{"item_id": "meal-1", "quantity": 1}],
        amount_minor=1599,
        currency="GBP",
        fulfilment_mode="delivery",
        idempotency_key="eats-order-0001",
    )
    assert result["order_id"] == ORDER
    assert result["payment_captured"] is False
    assert result["courier_dispatched"] is False
    assert connection.committed
    insert_sql = next(sql for sql, _ in connection.sql if "INSERT INTO oap_eats_orders" in sql)
    for field in ("merchant_id", "items", "amount_minor", "currency", "fulfilment_mode"):
        assert f"oap_eats_orders.{field}" in insert_sql
        assert f"EXCLUDED.{field}" in insert_sql


def test_eats_schema_requires_explicit_human_approval():
    with pytest.raises(RuntimeError, match="Explicit human approval"):
        oap_eats_store.init_schema()


def test_eats_schema_dry_run_is_not_green():
    status = oap_eats_store.init_schema(assume_yes=True, dry_run=True)
    assert status["schema_ready"] is False
    assert status["human_authority_final"] is True
