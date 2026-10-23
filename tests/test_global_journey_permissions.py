"""Session identity and HTTP permission guards for durable journey surfaces."""
from unittest.mock import Mock

import pytest

from mission_control import (
    global_journey_store,
    movement_operations,
    movement_routes,
    oap_eats_store,
)

IDENTITY = "11111111-1111-4111-8111-111111111111"
OTHER = "22222222-2222-4222-8222-222222222222"
RECORD = "33333333-3333-4333-8333-333333333333"
CANCEL = f"/movement/bookings/{RECORD}/cancel"
READS = [f"/movement/journeys/{RECORD}", f"/eats/orders/{RECORD}/delivery"]


@pytest.mark.parametrize("path", READS)
def test_journey_reads_require_session(anonymous_client, path):
    assert anonymous_client.get(path).status_code == 401


def test_cancel_requires_session(anonymous_client):
    assert anonymous_client.post(CANCEL).status_code == 401


def test_cancel_requires_csrf(client):
    assert client.post(CANCEL).status_code == 403


def test_cancel_rate_limit_precedes_store(client, csrf, monkeypatch):
    cancel = Mock()
    monkeypatch.setattr(movement_operations.STORE, "cancel_booking", cancel)
    monkeypatch.setattr(movement_routes.web_security.PUBLIC_WRITE_LIMITER, "allow", lambda _: False)
    assert client.post(CANCEL, headers={"X-OAP-CSRF": csrf["csrf_token"]}).status_code == 429
    cancel.assert_not_called()


def test_cancel_ignores_payload_owner_and_product_authority(client, csrf, monkeypatch):
    cancel = Mock(side_effect=PermissionError("booking_not_found"))
    monkeypatch.setattr(movement_operations.STORE, "cancel_booking", cancel)
    response = client.post(CANCEL, headers={"X-OAP-CSRF": csrf["csrf_token"]},
                           json={"member_identity_id": OTHER, "actor_identity_id": OTHER, "product_order_id": RECORD})
    assert response.status_code == 404
    assert cancel.call_args.kwargs == {"booking_id": RECORD, "member_identity_id": IDENTITY}


def test_journey_read_ignores_query_identity(client, monkeypatch):
    read = Mock(return_value=None)
    monkeypatch.setattr(global_journey_store, "read_journey", read)
    response = client.get(READS[0] + "?identity_id=" + OTHER)
    assert response.status_code == 404
    assert read.call_args.kwargs["identity_id"] == IDENTITY
    assert response.headers["Cache-Control"] == "no-store"


def test_delivery_read_uses_session_customer(client, monkeypatch):
    read = Mock(side_effect=PermissionError("order_delivery_not_verified"))
    monkeypatch.setattr(oap_eats_store.STORE, "read_delivery", read)
    response = client.get(READS[1] + "?customer_identity_id=" + OTHER)
    assert response.status_code == 403
    assert read.call_args.kwargs["customer_identity_id"] == IDENTITY
    assert "no-store" in response.headers["Cache-Control"]
