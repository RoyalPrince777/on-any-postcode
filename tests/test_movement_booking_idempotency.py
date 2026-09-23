"""Movement/Distribution retry safety: one key cannot expose or mutate another request."""
from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

import pytest

from mission_control import movement_operations, routing, web_security


MEMBER = "11111111-1111-4111-8111-111111111111"
BOOKING = "22222222-2222-4222-8222-222222222222"
OTHER_BOOKING = "33333333-3333-4333-8333-333333333333"
WHEN = datetime(2026, 9, 23, tzinfo=UTC)


def _place(label="Mitcham"):
    return {"label": label, "zone": "CR4", "latitude": 51.401, "longitude": -0.166}


class _Result:
    def __init__(self, value):
        self.value = value

    def fetchone(self):
        return self.value


class _Connection:
    def __init__(self, row):
        self.row = row
        self.sql = []
        self.committed = False

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def execute(self, sql, params):
        self.sql.append((sql, params))
        if "SELECT 1 FROM oap_movement_bookings" in sql:
            return _Result((1,))
        if "INSERT INTO oap_movement_" in sql:
            return _Result(self.row)
        raise AssertionError("Unexpected database operation")


def _booking(store):
    return store.create_booking(
        member_identity_id=MEMBER,
        service_type="ride",
        pickup=_place(),
        destination=_place("Brixton"),
        idempotency_key="movement-idempotency-test-001",
    )


@pytest.mark.parametrize("row", [None, (BOOKING, "ride", "REQUESTED", None, WHEN, WHEN)])
def test_booking_retry_binds_owner_and_immutable_payload(monkeypatch, row):
    connection = _Connection(row)
    monkeypatch.setattr(movement_operations.postgres_db, "connect", lambda **_: connection)
    if row is None:
        with pytest.raises(ValueError, match="^idempotency_conflict$"):
            _booking(movement_operations.STORE)
        assert not connection.committed
    else:
        result = _booking(movement_operations.STORE)
        assert result["booking_id"] == str(UUID(BOOKING))
        assert connection.committed
    sql, params = connection.sql[0]
    assert "ON CONFLICT (idempotency_key) DO UPDATE" in sql
    for field in (
        "member_identity_id", "service_type", "pickup", "destination",
        "scheduled_for", "route_snapshot"
    ):
        assert "oap_movement_bookings." + field in sql
        assert "EXCLUDED." + field in sql
    assert "IS NOT DISTINCT FROM" in sql
    assert params[0] == MEMBER


@pytest.mark.parametrize("row", [None, (BOOKING, "PROVIDER_REQUIRED", 123, "GBP", WHEN)])
def test_payment_intent_retry_binds_booking_owner_amount_currency(monkeypatch, row):
    connection = _Connection(row)
    monkeypatch.setattr(movement_operations.postgres_db, "connect", lambda **_: connection)
    operation = lambda: movement_operations.STORE.create_payment_intent(
        booking_id=BOOKING, member_identity_id=MEMBER,
        amount_minor=123, currency="GBP",
        idempotency_key="movement-payment-test-001",
    )
    if row is None:
        with pytest.raises(ValueError, match="^idempotency_conflict$"):
            operation()
        assert not connection.committed
    else:
        result = operation()
        assert result["payment_captured"] is False
        assert connection.committed
    sql, params = connection.sql[-1]
    assert "ON CONFLICT (idempotency_key) DO UPDATE" in sql
    for field in ("booking_id", "member_identity_id", "amount_minor", "currency"):
        assert "oap_movement_payment_intents." + field in sql
        assert "EXCLUDED." + field in sql
    assert params[:4] == (BOOKING, MEMBER, 123, "GBP")


def test_idempotency_conflict_api_does_not_disclose_other_booking(client, monkeypatch):
    token = "idempotency-csrf-test-12345678901234567890"
    with client.session_transaction() as session:
        session[web_security.CSRF_SESSION_KEY] = token
    monkeypatch.setattr(routing, "production_ready", lambda: False)

    def conflict(**_kwargs):
        raise ValueError("idempotency_conflict")

    monkeypatch.setattr(movement_operations.STORE, "create_booking", conflict)
    response = client.post(
        "/movement/bookings",
        headers={"X-OAP-CSRF": token, "Idempotency-Key": "movement-idempotency-test-002"},
        json={
            "service_type": "ride",
            "pickup": _place(),
            "destination": _place("Brixton"),
        },
    )
    assert response.status_code == 409
    assert response.get_json()["error"]["code"] == "idempotency_conflict"
    assert "booking_id" not in response.get_data(as_text=True)
    assert response.headers["Cache-Control"] == "no-store"
