from __future__ import annotations

from mission_control import (
    location_intelligence,
    movement_operations,
    movement_workspace,
    routing,
    web_security,
)


def _csrf_headers(client):
    token = "movement-workspace-csrf-test-token-1234567890"
    with client.session_transaction() as current_session:
        current_session[web_security.CSRF_SESSION_KEY] = token
    return {"X-OAP-CSRF": token}


def _snapshot():
    return {
        "bookings": [
            {
                "booking_id": "22222222-2222-4222-8222-222222222222",
                "service_type": "ride",
                "state": "REQUESTED",
                "pickup_label": "CR4 3AA",
                "pickup_zone": "CR4 3AA",
                "destination_label": "SW9 8AA",
                "destination_zone": "SW9 8AA",
                "scheduled_for": None,
                "route_distance_m": None,
                "route_duration_s": None,
                "route_ready": False,
                "created_at": "2026-08-26T00:00:00+00:00",
                "updated_at": "2026-08-26T00:00:00+00:00",
            }
        ],
        "availability": [
            {
                "role_type": "driver",
                "state": "ONLINE",
                "zone": "CR4",
                "available_until": None,
                "updated_at": "2026-08-26T00:00:00+00:00",
            }
        ],
        "worker_matches": [
            {
                "proposal_id": "33333333-3333-4333-8333-333333333333",
                "booking_id": "44444444-4444-4444-8444-444444444444",
                "worker_role": "driver",
                "proposal_state": "PROPOSED",
                "score": 1.0,
                "reason": "same_zone_available",
                "service_type": "ride",
                "booking_state": "MATCH_PROPOSED",
                "pickup_zone": "CR4",
                "destination_zone": "SW9",
                "created_at": "2026-08-26T00:00:00+00:00",
                "updated_at": "2026-08-26T00:00:00+00:00",
            }
        ],
        "member_matches": [],
        "certified_roles": ["MOVEMENT_DRIVER"],
        "precise_tracking_exposed": False,
        "other_worker_directory_exposed": False,
    }


def test_movement_workspace_requires_authenticated_identity(anonymous_client):
    response = anonymous_client.get("/movement/workspace")

    assert response.status_code == 302
    assert "/enter-my-world" in response.headers["Location"]
    assert "next=/movement/workspace" in response.headers["Location"]


def test_movement_workspace_renders_only_private_operational_projection(
    client, monkeypatch
):
    monkeypatch.setattr(movement_workspace, "snapshot", lambda identity: _snapshot())
    monkeypatch.setattr(
        routing,
        "status",
        lambda: {
            "production_ready": False,
            "runtime_verified": True,
            "provider_tier": "verification_only",
        },
    )

    response = client.get("/movement/workspace")
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "My Movement" in html
    assert "CR4 3AA" in html
    assert "Find certified match" in html
    assert "Accept match" in html
    assert "Go Online" in html
    assert "verification-only" in html
    assert "member_identity_id" not in html
    assert "worker_identity_id" not in html
    assert "latitude" not in html.lower()
    assert "longitude" not in html.lower()


def test_booking_from_place_queries_does_not_use_verification_only_routing(
    client, monkeypatch
):
    headers = _csrf_headers(client)
    resolved = {
        "query": "CR4 3AA",
        "postcode": "CR4 3AA",
        "borough": "Merton",
        "county": "London",
        "country": "United Kingdom",
        "continent": "Europe",
        "latitude": 51.401,
        "longitude": -0.166,
        "provider": "UK postcode service",
    }

    def lookup(query):
        if query == "SW9 8AA":
            return {
                **resolved,
                "query": query,
                "postcode": query,
                "latitude": 51.462,
                "longitude": -0.115,
            }
        return resolved

    monkeypatch.setattr(location_intelligence, "lookup", lookup)
    monkeypatch.setattr(routing, "production_ready", lambda: False)

    def route_must_not_run(**kwargs):
        raise AssertionError("verification-only route must not enrich booking")

    monkeypatch.setattr(routing, "route", route_must_not_run)

    captured = {}

    def create_booking(**kwargs):
        captured.update(kwargs)
        return {
            "booking_id": "22222222-2222-4222-8222-222222222222",
            "service_type": "ride",
            "state": "REQUESTED",
            "scheduled_for": None,
            "created_at": "2026-08-26T00:00:00+00:00",
            "updated_at": "2026-08-26T00:00:00+00:00",
        }

    monkeypatch.setattr(movement_operations.STORE, "create_booking", create_booking)

    response = client.post(
        "/movement/bookings",
        headers=headers,
        json={
            "service_type": "ride",
            "pickup_query": "CR4 3AA",
            "destination_query": "SW9 8AA",
            "idempotency_key": "workspace-booking-test-0001",
        },
    )

    assert response.status_code == 201
    assert captured["pickup"]["label"] == "CR4 3AA"
    assert captured["destination"]["label"] == "SW9 8AA"
    assert captured["route_snapshot"] is None


def test_public_movement_links_to_private_workspace(client):
    response = client.get("/movement")
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert 'href="/movement/workspace"' in html
    assert "My Movement" in html
