from mission_control import (
    map_live_pattern,
    movement_intelligence,
    movement_proof,
    routing,
)


def _route_ready():
    return {
        "configured": True,
        "runtime_verified": True,
        "provider_tier": "production_candidate",
        "provider_ownership": "oap_owned",
        "oap_owned_endpoint": True,
        "geometry_exposed": True,
        "road_vector_tiles": True,
        "production_provider_approved": False,
        "production_capacity_approved": False,
        "production_monitoring_approved": False,
        "production_gate_approved": False,
        "production_ready": False,
        "last_error": None,
    }


def test_movement_truth_status_uses_runtime_geometry_without_unlocking_execution(monkeypatch):
    monkeypatch.setattr(routing, "status", _route_ready)
    monkeypatch.setattr(
        map_live_pattern,
        "status",
        lambda: {
            "authority_feed": "Transport for London Open Data",
            "authority_verified_feed": True,
        },
    )

    evidence = movement_proof.last_route_status()
    assert evidence["route_geometry_proven"] is True
    assert evidence["live_traffic_proven"] is True
    assert evidence["routing_provider_ownership"] == "oap_owned"
    assert evidence["dispatch_enabled"] is False
    assert evidence["payment_capture_enabled"] is False
    assert evidence["hidden_tracking"] is False


def test_movement_intelligence_separates_software_from_production(monkeypatch):
    monkeypatch.setattr(routing, "status", _route_ready)
    monkeypatch.setattr(
        map_live_pattern,
        "status",
        lambda: {
            "authority_feed": "Transport for London Open Data",
            "authority_verified_feed": True,
        },
    )
    state = movement_intelligence.movement_intelligence_status()
    assert state["software_navigation_ready"] is True
    assert state["route_geometry_proven"] is True
    assert state["live_disruption_authority_proven"] is True
    assert state["production_navigation_ready"] is False

    approved = _route_ready()
    approved.update(
        production_provider_approved=True,
        production_capacity_approved=True,
        production_monitoring_approved=True,
        production_gate_approved=True,
        production_ready=True,
    )
    monkeypatch.setattr(routing, "status", lambda: approved)
    state = movement_intelligence.movement_intelligence_status()
    assert state["software_navigation_ready"] is True
    assert state["production_navigation_ready"] is True


def test_missing_runtime_geometry_stays_fail_closed(monkeypatch):
    blocked = _route_ready()
    blocked.update(runtime_verified=False, geometry_exposed=False, last_error="routing_http_429")
    monkeypatch.setattr(routing, "status", lambda: blocked)
    monkeypatch.setattr(
        map_live_pattern,
        "status",
        lambda: {
            "authority_feed": "Transport for London Open Data",
            "authority_verified_feed": False,
        },
    )
    evidence = movement_proof.last_route_status()
    state = movement_intelligence.movement_intelligence_status()
    assert evidence["route_geometry_proven"] is False
    assert evidence["live_traffic_proven"] is False
    assert state["software_navigation_ready"] is False
    assert state["production_navigation_ready"] is False
