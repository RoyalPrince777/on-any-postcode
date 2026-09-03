from __future__ import annotations

from mission_control import movement_operations, routing


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
    expected = {
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
    for key, value in expected.items():
        assert payload[key] == value

    assert payload["movement_intelligence_architecture_passed"] is True
    assert payload["movement_intelligence_component_count"] == 11
    assert payload["movement_intelligence_first_party"] is True
    assert payload["movement_intelligence_production_navigation_ready"] is False
    intelligence = payload["movement_intelligence"]
    assert intelligence["name"] == "OAP Movement Intelligence"
    assert intelligence["production_navigation_ready"] is False
    assert intelligence["first_party_policy"]["oap_controlled_route_engine_required"] is True
