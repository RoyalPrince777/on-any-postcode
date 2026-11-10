from mission_control import live_road_intelligence, map_live_pattern


def test_route_state_fails_closed_without_fresh_evidence(monkeypatch):
    monkeypatch.setattr(map_live_pattern, "reports", lambda query=None: [])
    monkeypatch.setattr(live_road_intelligence, "observations", lambda road=None: [])

    state = live_road_intelligence.route_state(
        {"duration_s": 600, "roads": ["London Road"]},
        "Mitcham",
    )

    assert state["state"] == "unknown"
    assert state["live_claim_allowed"] is False
    assert state["eta_multiplier"] == 1.0
    assert state["adjusted_duration_s"] == 600
    assert state["reroute_recommended"] is False


def test_authority_closure_adjusts_eta_and_recommends_reroute(monkeypatch):
    monkeypatch.setattr(
        map_live_pattern,
        "reports",
        lambda query=None: [{
            "id": "tfl-1",
            "road": "London Road",
            "area": "Mitcham",
            "kind": "closure",
            "note": "Road closed",
            "source": "Transport for London Open Data",
            "authority_verified": True,
            "has_closures": True,
            "updated_at": "2026-10-02T20:00:00Z",
        }],
    )
    monkeypatch.setattr(live_road_intelligence, "observations", lambda road=None: [])

    state = live_road_intelligence.route_state(
        {"duration_s": 600, "roads": ["London Road"]},
        "Mitcham",
    )

    assert state["state"] == "closed"
    assert state["authority_evidence_present"] is True
    assert state["live_claim_allowed"] is True
    assert state["eta_multiplier"] == 2.0
    assert state["adjusted_duration_s"] == 1200
    assert state["reroute_recommended"] is True


def test_movement_observation_never_requires_precise_location(monkeypatch):
    monkeypatch.setattr(map_live_pattern, "reports", lambda query=None: [])
    item = live_road_intelligence.record_observation(
        road="A236",
        state="slow",
        speed_kph=18,
    )

    assert item["road"] == "A236"
    assert item["state"] == "slow"
    assert item["speed_kph"] == 18
    assert item["precise_device_location_stored"] is False


def test_live_road_status_separates_software_readiness_from_external_coverage(monkeypatch):
    monkeypatch.setattr(
        map_live_pattern,
        "status",
        lambda: {"authority_verified_feed": True},
    )

    status = live_road_intelligence.status()

    assert status["observation_collector_ready"] is True
    assert status["road_state_aggregator_ready"] is True
    assert status["dynamic_eta_ready"] is True
    assert status["traffic_layer_ready"] is True
    assert status["reroute_signal_ready"] is True
    assert status["authority_feed_verified"] is True
    assert status["continuous_speed_coverage_proven"] is False
    assert status["uk_wide_live_traffic_proven"] is False
    assert status["vehicle_telemetry_integration_proven"] is False


def test_explicit_authority_free_state_does_not_inflate_eta(monkeypatch):
    monkeypatch.setattr(
        map_live_pattern,
        "reports",
        lambda query=None: [{
            "id": "tfl-road-a23",
            "road": "A23",
            "area": "Greater London",
            "kind": "delay",
            "road_state": "free",
            "note": "No exceptional delays",
            "source": "Transport for London Road Status",
            "authority_verified": True,
            "has_closures": False,
            "updated_at": "2026-10-03T00:00:00Z",
        }],
    )
    monkeypatch.setattr(live_road_intelligence, "observations", lambda road=None: [])

    state = live_road_intelligence.route_state(
        {"duration_s": 600, "roads": ["A23"]},
        "A23",
    )

    assert state["state"] == "free"
    assert state["live_claim_allowed"] is True
    assert state["eta_multiplier"] == 1.0
    assert state["adjusted_duration_s"] == 600


def test_explicit_authority_heavy_state_adjusts_eta(monkeypatch):
    monkeypatch.setattr(
        map_live_pattern,
        "reports",
        lambda query=None: [{
            "id": "tfl-road-a406",
            "road": "North Circular (A406)",
            "area": "Greater London",
            "kind": "delay",
            "road_state": "heavy",
            "note": "Serious delays",
            "source": "Transport for London Road Status",
            "authority_verified": True,
            "has_closures": False,
            "updated_at": "2026-10-03T00:00:00Z",
        }],
    )
    monkeypatch.setattr(live_road_intelligence, "observations", lambda road=None: [])

    state = live_road_intelligence.route_state(
        {"duration_s": 600, "roads": ["A406"]},
        "A406",
    )

    assert state["state"] == "heavy"
    assert state["eta_multiplier"] == 1.3
    assert state["adjusted_duration_s"] == 780


def test_live_road_status_keeps_external_sources_evidence_only(monkeypatch):
    monkeypatch.setattr(
        map_live_pattern,
        "status",
        lambda: {"authority_verified_feed": True},
    )

    status = live_road_intelligence.status()

    assert status["intelligence_owner"] == "ON ANY POSTCODE"
    assert status["decision_engine"] == "OAP Live Road Intelligence"
    assert status["external_sources_are_evidence_only"] is True
    assert status["external_source_decision_authority"] is False
    assert status["external_source_routing_authority"] is False


def test_route_evidence_never_grants_external_decision_authority(monkeypatch):
    monkeypatch.setattr(
        map_live_pattern,
        "reports",
        lambda query=None: [{
            "id": "tfl-road-a23",
            "road": "A23",
            "area": "Greater London",
            "kind": "delay",
            "road_state": "slow",
            "note": "Minor delays",
            "source": "Transport for London Road Status",
            "source_role": "external_evidence_only",
            "external_source": True,
            "oap_decision_authority": False,
            "authority_verified": True,
            "has_closures": False,
            "updated_at": "2026-10-03T00:00:00Z",
        }],
    )
    monkeypatch.setattr(live_road_intelligence, "observations", lambda road=None: [])

    state = live_road_intelligence.route_state(
        {"duration_s": 600, "roads": ["A23"]},
        "A23",
    )

    assert state["reports"][0]["source_role"] == "external_evidence_only"
    assert state["reports"][0]["external_source"] is True
    assert state["reports"][0]["oap_decision_authority"] is False
