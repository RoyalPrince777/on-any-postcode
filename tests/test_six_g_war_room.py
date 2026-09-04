from mission_control import six_g_war_room


def _runtime(*, connected: bool, testbed: bool, production_6g: bool):
    return {
        "mode": "production",
        "demo_mode": False,
        "simulation_success_allowed": False,
        "production_software_ready": connected,
        "host": {
            "runtime_connectivity_present": connected,
        },
        "radio_evidence": {
            "valid": testbed or production_6g,
            "testbed_ready": testbed,
            "reason": "radio evidence verified"
            if testbed or production_6g
            else "radio evidence not configured",
        },
        "6g_intelligence_runtime_ready": connected,
        "6g_testbed_ready": testbed,
        "6g_production_network_ready": production_6g,
        "imt_2030_standard_finalized": production_6g,
        "imt_2030_status_verified_date": "2026-09-04",
        "imt_2030_target_standard_year": 2030,
        "network_execution_authority": False,
        "human_authority_final": True,
    }


def test_war_room_exposes_official_scenarios_and_capabilities(monkeypatch):
    monkeypatch.setattr(
        six_g_war_room,
        "connectivity_runtime_status",
        lambda: _runtime(connected=True, testbed=False, production_6g=False),
    )
    status = six_g_war_room.six_g_war_room_status()

    assert status["mode"] == "production_evidence_review"
    assert status["demo_mode"] is False
    assert status["simulation_success_allowed"] is False
    assert len(status["usage_scenarios"]) == 6
    assert len(status["capabilities"]) == 15
    assert len(status["feature_matrix"]) == 8
    assert len(status["red_team"]) == 7
    assert status["network_execution_authority"] is False
    assert status["autonomous_radio_control"] is False
    assert status["autonomous_esim_provisioning"] is False
    assert status["human_authority_final"] is True


def test_production_software_does_not_fake_6g_radio(monkeypatch):
    monkeypatch.setattr(
        six_g_war_room,
        "connectivity_runtime_status",
        lambda: _runtime(connected=True, testbed=False, production_6g=False),
    )
    status = six_g_war_room.six_g_war_room_status()
    features = {item["id"]: item for item in status["feature_matrix"]}

    assert features["runtime_observation"]["ready"] is True
    assert features["network_selection"]["ready"] is True
    assert features["resilience"]["ready"] is True
    assert features["edge_ai"]["ready"] is True
    assert features["signed_radio_evidence"]["ready"] is False
    assert features["testbed_gate"]["ready"] is False
    assert features["standards_gate"]["ready"] is False
    assert all(
        item["standardized_6g_ready"] is False
        for item in status["usage_scenarios"]
    )


def test_verified_testbed_is_distinct_from_standardized_6g(monkeypatch):
    monkeypatch.setattr(
        six_g_war_room,
        "connectivity_runtime_status",
        lambda: _runtime(connected=True, testbed=True, production_6g=False),
    )
    status = six_g_war_room.six_g_war_room_status()
    features = {item["id"]: item for item in status["feature_matrix"]}

    assert features["signed_radio_evidence"]["ready"] is True
    assert features["testbed_gate"]["ready"] is True
    assert features["standards_gate"]["ready"] is False
    assert all(
        item["state"] == "verified_testbed" for item in status["usage_scenarios"]
    )


def test_standardized_6g_requires_explicit_runtime_proof(monkeypatch):
    monkeypatch.setattr(
        six_g_war_room,
        "connectivity_runtime_status",
        lambda: _runtime(connected=True, testbed=False, production_6g=True),
    )
    status = six_g_war_room.six_g_war_room_status()
    features = {item["id"]: item for item in status["feature_matrix"]}

    assert features["standards_gate"]["ready"] is True
    assert all(
        item["standardized_6g_ready"] is True
        for item in status["usage_scenarios"]
    )
    assert all(item["standards_certified"] for item in status["capabilities"])
