from __future__ import annotations

import json

import pytest

from mission_control import movement_operations, routing, web_security


def _csrf_headers(client):
    token = "movement-csrf-test-token-12345678901234567890"
    with client.session_transaction() as current_session:
        current_session[web_security.CSRF_SESSION_KEY] = token
    return {"X-OAP-CSRF": token}


def _place(label="Mitcham", zone="CR4", latitude=51.401, longitude=-0.166):
    return {
        "label": label,
        "zone": zone,
        "latitude": latitude,
        "longitude": longitude,
    }


def test_movement_schema_is_ordered_idempotent_and_has_eight_private_tables():
    assert movement_operations.MOVEMENT_MIGRATION_VERSION == "0005_movement_operations"
    assert len(movement_operations.MOVEMENT_TABLES) == 8
    assert len(movement_operations.MOVEMENT_MIGRATION_CHECKSUM) == 64

    sql = movement_operations.migration_sql()
    for table in movement_operations.MOVEMENT_TABLES:
        assert table in sql
    assert movement_operations.MOVEMENT_MIGRATION_VERSION in sql
    assert movement_operations.MOVEMENT_MIGRATION_CHECKSUM in sql
    assert "DROP TABLE" not in sql.upper()
    assert "DROP COLUMN" not in sql.upper()


def test_movement_schema_requires_explicit_human_approval():
    with pytest.raises(RuntimeError, match="Explicit human approval required"):
        movement_operations.init_movement_schema()


def test_place_normalization_is_bounded_and_private_data_shaped():
    place = movement_operations.normalize_place(_place(), name="pickup")
    assert place == {
        "label": "Mitcham",
        "zone": "CR4",
        "latitude": 51.401,
        "longitude": -0.166,
    }

    with pytest.raises(ValueError, match="invalid_pickup_latitude"):
        movement_operations.normalize_place(
            _place(latitude=100),
            name="pickup",
        )


def test_private_movement_writes_require_authentication(anonymous_client):
    response = anonymous_client.post(
        "/movement/bookings",
        json={
            "service_type": "ride",
            "pickup": _place(),
            "destination": _place("Brixton", "SW9", 51.462, -0.115),
            "idempotency_key": "booking-auth-test-0001",
        },
    )
    assert response.status_code == 401
    assert response.get_json()["error"]["code"] == "authentication_required"


def test_private_movement_writes_require_csrf(client):
    response = client.post(
        "/movement/bookings",
        json={
            "service_type": "ride",
            "pickup": _place(),
            "destination": _place("Brixton", "SW9", 51.462, -0.115),
            "idempotency_key": "booking-csrf-test-0001",
        },
    )
    assert response.status_code == 403
    assert response.get_json()["error"]["code"] == "csrf_failed"


def test_authenticated_booking_persists_without_fake_route_provider(
    client, monkeypatch
):
    headers = _csrf_headers(client)
    headers["Idempotency-Key"] = "booking-create-test-0001"
    monkeypatch.setattr(routing, "configured", lambda: False)

    def fake_create_booking(**kwargs):
        assert kwargs["service_type"] == "ride"
        assert kwargs["route_snapshot"] is None
        assert kwargs["idempotency_key"] == "booking-create-test-0001"
        return {
            "booking_id": "22222222-2222-4222-8222-222222222222",
            "service_type": "ride",
            "state": "REQUESTED",
            "scheduled_for": None,
            "created_at": "2026-08-25T20:00:00+00:00",
            "updated_at": "2026-08-25T20:00:00+00:00",
        }

    monkeypatch.setattr(
        movement_operations.STORE,
        "create_booking",
        fake_create_booking,
    )

    response = client.post(
        "/movement/bookings",
        headers=headers,
        json={
            "service_type": "ride",
            "pickup": _place(),
            "destination": _place("Brixton", "SW9", 51.462, -0.115),
        },
    )
    payload = response.get_json()

    assert response.status_code == 201
    assert payload["booking"]["state"] == "REQUESTED"


def test_private_route_api_never_claims_dispatch_or_geometry(client, monkeypatch):
    headers = _csrf_headers(client)
    monkeypatch.setattr(
        routing,
        "route",
        lambda **kwargs: {
            "distance_m": 1500.0,
            "duration_s": 420.0,
            "profile": kwargs["profile"],
            "provider": "OSRM-compatible routing",
            "geometry_exposed": False,
            "dispatch_performed": False,
        },
    )

    response = client.post(
        "/movement/route",
        headers=headers,
        json={
            "pickup": _place(),
            "destination": _place("Brixton", "SW9", 51.462, -0.115),
            "profile": "driving",
        },
    )
    route = response.get_json()["route"]

    assert response.status_code == 200
    assert route["geometry_exposed"] is False
    assert route["dispatch_performed"] is False
    assert "geometry" not in route


def test_worker_availability_fails_closed_without_certified_role(client, monkeypatch):
    headers = _csrf_headers(client)

    def reject(**kwargs):
        raise PermissionError("certified_movement_role_required")

    monkeypatch.setattr(movement_operations.STORE, "set_availability", reject)
    response = client.post(
        "/movement/availability",
        headers=headers,
        json={"role_type": "driver", "state": "ONLINE", "zone": "CR4"},
    )

    assert response.status_code == 403
    assert response.get_json()["error"]["code"] == "certified_movement_role_required"


def test_matching_is_a_proposal_not_external_dispatch(client, monkeypatch):
    headers = _csrf_headers(client)
    monkeypatch.setattr(
        movement_operations.STORE,
        "propose_match",
        lambda **kwargs: {
            "proposal_id": "33333333-3333-4333-8333-333333333333",
            "worker_identity_id": "44444444-4444-4444-8444-444444444444",
            "worker_role": "driver",
            "state": "PROPOSED",
            "score": 1.0,
            "reason": "same_zone_available",
            "created_at": "2026-08-25T20:00:00+00:00",
            "dispatch_performed": False,
        },
    )

    response = client.post(
        "/movement/bookings/22222222-2222-4222-8222-222222222222/match",
        headers=headers,
    )
    match = response.get_json()["match"]

    assert response.status_code == 201
    assert match["state"] == "PROPOSED"
    assert match["dispatch_performed"] is False


def test_tracking_consent_and_point_are_private_and_expiring(client, monkeypatch):
    headers = _csrf_headers(client)
    monkeypatch.setattr(
        movement_operations.STORE,
        "grant_tracking_consent",
        lambda **kwargs: {
            "state": "ACTIVE",
            "expires_at": "2026-08-25T22:00:00+00:00",
            "updated_at": "2026-08-25T21:00:00+00:00",
            "scope": "own_location_only",
        },
    )
    monkeypatch.setattr(
        movement_operations.STORE,
        "record_tracking_point",
        lambda **kwargs: {
            "point_id": "55555555-5555-4555-8555-555555555555",
            "recorded_at": "2026-08-25T21:00:00+00:00",
            "expires_at": "2026-08-25T22:00:00+00:00",
            "publicly_visible": False,
        },
    )

    booking = "22222222-2222-4222-8222-222222222222"
    consent = client.post(
        f"/movement/bookings/{booking}/tracking/consent",
        headers=headers,
        json={"expires_at": "2026-08-25T22:00:00+00:00"},
    )
    point = client.post(
        f"/movement/bookings/{booking}/tracking/points",
        headers=headers,
        json={"latitude": 51.4, "longitude": -0.2},
    )

    assert consent.status_code == 200
    assert consent.get_json()["consent"]["scope"] == "own_location_only"
    assert point.status_code == 201
    assert point.get_json()["point"]["publicly_visible"] is False


def test_esim_request_cannot_claim_activation(client, monkeypatch):
    headers = _csrf_headers(client)
    monkeypatch.setattr(
        movement_operations.STORE,
        "request_esim_connectivity",
        lambda **kwargs: {
            "request_id": "66666666-6666-4666-8666-666666666666",
            "state": "PROVIDER_REQUIRED",
            "created_at": "2026-08-25T21:00:00+00:00",
            "activation_performed": False,
            "carrier_identifier_exposed": False,
        },
    )

    response = client.post(
        "/movement/esim/requests",
        headers=headers,
        json={"purpose": "Driver work connectivity"},
    )
    request_body = response.get_json()["esim_request"]

    assert response.status_code == 201
    assert request_body["state"] == "PROVIDER_REQUIRED"
    assert request_body["activation_performed"] is False
    assert request_body["carrier_identifier_exposed"] is False


def test_payment_intent_cannot_capture_money(client, monkeypatch):
    headers = _csrf_headers(client)
    headers["Idempotency-Key"] = "payment-intent-test-0001"
    monkeypatch.setattr(
        movement_operations.STORE,
        "create_payment_intent",
        lambda **kwargs: {
            "intent_id": "77777777-7777-4777-8777-777777777777",
            "state": "PROVIDER_REQUIRED",
            "amount_minor": 1200,
            "currency": "GBP",
            "created_at": "2026-08-25T21:00:00+00:00",
            "payment_captured": False,
        },
    )

    response = client.post(
        "/movement/bookings/22222222-2222-4222-8222-222222222222/payment-intents",
        headers=headers,
        json={"amount_minor": 1200, "currency": "GBP"},
    )
    intent = response.get_json()["payment_intent"]

    assert response.status_code == 201
    assert intent["state"] == "PROVIDER_REQUIRED"
    assert intent["payment_captured"] is False


def test_trip_channel_is_only_a_link_up_binding(client, monkeypatch):
    headers = _csrf_headers(client)
    monkeypatch.setattr(
        movement_operations.STORE,
        "ensure_trip_channel",
        lambda **kwargs: {
            "channel_id": "88888888-8888-4888-8888-888888888888",
            "state": "PENDING_LINK_UP",
            "linkup_conversation_id": None,
            "created_at": "2026-08-25T21:00:00+00:00",
            "updated_at": "2026-08-25T21:00:00+00:00",
            "message_store_duplicated": False,
        },
    )

    response = client.post(
        "/movement/bookings/22222222-2222-4222-8222-222222222222/link-up",
        headers=headers,
    )
    channel = response.get_json()["channel"]

    assert response.status_code == 201
    assert channel["state"] == "PENDING_LINK_UP"
    assert channel["message_store_duplicated"] is False


def test_public_movement_status_does_not_expose_private_operation_fields(client):
    payload = client.get("/movement/status").get_json()
    serialized = json.dumps(payload).lower()

    for forbidden in (
        "member_identity_id",
        "worker_identity_id",
        "latitude",
        "longitude",
        "provider_reference",
        "linkup_conversation_id",
    ):
        assert forbidden not in serialized
