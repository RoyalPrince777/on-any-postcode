from __future__ import annotations

import json

from mission_control import movement


def test_movement_architecture_is_unique_and_fail_closed():
    validation = movement.validate_movement_architecture()

    assert validation["passed"] is True
    assert validation["errors"] == []
    assert validation["checks"] == {
        "services": 5,
        "roles": 5,
        "duplicate_service_ids": 0,
        "duplicate_role_ids": 0,
        "privileged_controls_enabled": 0,
        "provider_connected": False,
    }


def test_movement_contains_ride_ebike_delivery_booking_and_tracking():
    service_ids = {service["id"] for service in movement.MOVEMENT_SERVICES}

    assert service_ids == {"ride", "ebike", "delivery", "booking", "tracking"}
    role_ids = {role["id"] for role in movement.MOVEMENT_ROLES}
    assert {"driver", "rider", "courier", "member", "merchant"} == role_ids


def test_esim_controls_remain_provider_controlled_and_off():
    controls = movement.ESIM_CONNECTIVITY["provider_controls"]

    assert controls == {
        "provider_connected": False,
        "profile_activation_enabled": False,
        "profile_deactivation_enabled": False,
        "carrier_switch_enabled": False,
        "remote_profile_install_enabled": False,
    }
    assert movement.EXECUTION_BOUNDARY["esim_activation_enabled"] is False
    assert movement.EXECUTION_BOUNDARY["dispatch_enabled"] is False
    assert movement.EXECUTION_BOUNDARY["payment_enabled"] is False
    assert movement.EXECUTION_BOUNDARY["live_tracking_enabled"] is False
    assert movement.EXECUTION_BOUNDARY["human_approval_required"] is True


def test_public_movement_projection_contains_no_carrier_secrets():
    public = json.dumps(movement.get_public_movement()).lower()

    for sensitive_key in (
        "iccid",
        "eid_number",
        "activation_code",
        "smdp_address",
        "carrier_token",
        "subscriber_key",
        "precise_location",
    ):
        assert sensitive_key not in public


def test_public_movement_route_is_read_only(client):
    response = client.get("/movement")
    page = response.get_data(as_text=True)

    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    assert "OAP Movement" in page
    assert "OAP Ride" in page
    assert "OAP E-Bike" in page
    assert "OAP Delivery" in page
    assert "Booking" in page
    assert "Track" in page
    assert "OAP eSIM Connectivity" in page
    assert "Provider not connected" in page
    assert "No carrier profile activation" in page
    assert 'method="post"' not in page.lower()
    assert client.post("/movement").status_code == 405


def test_public_movement_status_is_coarse_and_fail_closed(client):
    response = client.get("/movement/status")
    payload = response.get_json()

    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    assert payload == {
        "product": "OAP Movement",
        "architecture_passed": True,
        "services": 5,
        "roles": 5,
        "esim_provider_connected": False,
        "dispatch_enabled": False,
        "payment_enabled": False,
        "live_tracking_enabled": False,
        "esim_activation_enabled": False,
        "human_approval_required": True,
    }


def test_spot_movement_surface_links_into_dedicated_product(client):
    page = client.get("/the-spot/movement-delivery").get_data(as_text=True)

    assert "OAP Movement" in page
    assert "🚗 Ride" in page
    assert "🚲 E-Bike" in page
    assert "📦 Delivery" in page
    assert "📶 eSIM" in page
    assert 'href="/movement"' in page
    assert "Carrier activation, dispatch, payment and live tracking stay off" in page
