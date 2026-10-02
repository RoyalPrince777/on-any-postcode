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
