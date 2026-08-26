from __future__ import annotations

import json

from mission_control import movement, movement_operations, routing


def test_movement_architecture_is_unique_ordered_and_fail_closed():
    validation = movement.validate_movement_architecture()

    assert validation["passed"] is True
    assert validation["errors"] == []
    assert validation["checks"] == {
        "services": 5,
        "roles": 5,
        "ordered_steps": 8,
        "duplicate_service_ids": 0,
        "duplicate_role_ids": 0,
        "duplicate_order_ids": 0,
        "privileged_controls_enabled": 0,
    }


def test_movement_contains_services_roles_and_exact_build_order():
    service_ids = {service["id"] for service in movement.MOVEMENT_SERVICES}
    assert service_ids == {"ride", "ebike", "delivery", "booking", "tracking"}

    role_ids = {role["id"] for role in movement.MOVEMENT_ROLES}
    assert {"driver", "rider", "courier", "member", "merchant"} == role_ids

    assert [item["id"] for item in movement.MOVEMENT_BUILD_ORDER] == [
        "routing",
        "booking",
        "availability",
        "matching",
        "tracking",
        "esim",
        "payments",
        "linkup",
    ]


def test_external_esim_dispatch_payment_and_public_tracking_remain_off():
    controls = movement.ESIM_CONNECTIVITY["provider_controls"]

    assert controls == {
        "provider_connected": False,
        "profile_activation_enabled": False,
        "profile_deactivation_enabled": False,
        "carrier_switch_enabled": False,
        "remote_profile_install_enabled": False,
    }
    assert movement.EXECUTION_BOUNDARY["esim_activation_enabled"] is False
    assert movement.EXECUTION_BOUNDARY["external_dispatch_enabled"] is False
    assert movement.EXECUTION_BOUNDARY["payment_capture_enabled"] is False
    assert movement.EXECUTION_BOUNDARY["public_tracking_enabled"] is False
    assert movement.EXECUTION_BOUNDARY["human_approval_required"] is True


def test_public_movement_projection_contains_no_carrier_or_tracking_secrets():
    public = json.dumps(movement.get_public_movement()).lower()

    for sensitive_key in (
        "iccid",
        "eid_number",
        "activation_code",
        "smdp_address",
        "carrier_token",
        "subscriber_key",
        "tracking_points",
        "provider_reference",
    ):
        assert sensitive_key not in public


def test_public_movement_route_has_no_write_controls(client):
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
    assert "Movement operations sequence" in page
    assert "Step 1" in page
    assert "Step 8" in page
    assert "Provider not connected" in page
    assert "No carrier profile activation" in page
    assert 'method="post"' not in page.lower()
    assert client.post("/movement").status_code == 405


def test_public_movement_status_is_coarse_and_separates_readiness(
    client, monkeypatch
):
    monkeypatch.setattr(
        movement_operations,
        "movement_schema_status",
        lambda: {"schema_ready": False},
    )
    monkeypatch.setattr(
        routing,
        "status",
        lambda: {
            "configured": False,
            "runtime_verified": False,
            "provider_tier": "unconfigured",
            "production_provider_approved": False,
            "production_capacity_approved": False,
            "production_monitoring_approved": False,
            "production_ready": False,
        },
    )

    response = client.get("/movement/status")
    payload = response.get_json()

    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    assert payload == {
        "product": "OAP Movement",
        "architecture_passed": True,
        "ordered_steps": 8,
        "routing_adapter_configured": False,
        "routing_runtime_verified": False,
        "routing_provider_tier": "unconfigured",
        "routing_production_provider_approved": False,
        "routing_capacity_approved": False,
        "routing_monitoring_approved": False,
        "routing_production_ready": False,
        "booking_persistence_ready": False,
        "availability_store_ready": False,
        "match_proposal_store_ready": False,
        "tracking_consent_store_ready": False,
        "esim_request_store_ready": False,
        "payment_intent_store_ready": False,
        "linkup_trip_binding_ready": False,
        "external_dispatch_enabled": False,
        "payment_capture_enabled": False,
        "esim_activation_enabled": False,
        "public_tracking_enabled": False,
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
