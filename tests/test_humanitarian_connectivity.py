from mission_control import humanitarian_connectivity, technology_intelligence


def test_humanitarian_status_is_civilian_production_and_non_executing():
    status = humanitarian_connectivity.humanitarian_connectivity_status()

    assert status["name"] == "Humanitarian Connectivity Intelligence"
    assert status["legacy_name"] == "International Humanitarian Connectivity Intelligence"
    assert status["parent"] == "International Humanitarian Intelligence"
    assert status["mode"] == "civilian_emergency_production"
    assert status["demo_mode"] is False
    assert status["civilian_only"] is True
    assert status["military_command"] is False
    assert status["targeting"] is False
    assert status["surveillance"] is False
    assert status["weapon_support"] is False
    assert status["offensive_cyber"] is False
    assert status["precise_location_default"] is False
    assert status["autonomous_transmission"] is False
    assert status["network_execution_authority"] is False
    assert status["human_authority_final"] is True
    assert status["feature_count"] == 9
    assert len(status["priorities"]) == 7
    assert status["map_intelligence_bound"] is True
    assert status["maps"]["architecture_ready"] is True


def test_life_safety_message_is_prepared_not_transmitted():
    result = humanitarian_connectivity.prepare_humanitarian_message(
        purpose="life_safety",
        text="Civilians need urgent evacuation assistance after building damage.",
        approximate_area="north district",
    )

    assert result["accepted"] is True
    assert result["priority"] == 0
    assert result["store_and_forward"] is True
    assert result["precise_location_stored"] is False
    assert result["transmitted"] is False
    assert result["requires_human_review"] is True


def test_legitimate_humanitarian_report_can_describe_airstrike_harm():
    result = humanitarian_connectivity.prepare_humanitarian_message(
        purpose="medical",
        text="Hospital damaged by an airstrike; civilians need medical supplies.",
    )

    assert result["accepted"] is True
    assert result["reason"] == "prepared"


def test_military_targeting_request_is_rejected():
    result = humanitarian_connectivity.prepare_humanitarian_message(
        purpose="aid_coordination",
        text="Send target coordinates for strike planning.",
    )

    assert result["accepted"] is False
    assert result["reason"] == "civilian_distinction_guard"
    assert result["transmitted"] is False


def test_public_warning_requires_verified_source():
    blocked = humanitarian_connectivity.prepare_humanitarian_message(
        purpose="public_warning",
        text="Move away from the flooded river area.",
        source_verified=False,
    )
    allowed = humanitarian_connectivity.prepare_humanitarian_message(
        purpose="public_warning",
        text="Move away from the flooded river area.",
        source_verified=True,
    )

    assert blocked["accepted"] is False
    assert blocked["reason"] == "source_verification_required"
    assert allowed["accepted"] is True


def test_technology_intelligence_exposes_humanitarian_as_supported_child():
    status = technology_intelligence.technology_intelligence_status()
    humanitarian = status["international_humanitarian_connectivity"]
    umbrella = status["international_humanitarian_intelligence"]
    capability_ids = tuple(item["id"] for item in status["connectivity"]["capabilities"])

    assert "humanitarian_emergency" in capability_ids
    assert humanitarian["name"] == "Humanitarian Connectivity Intelligence"
    assert humanitarian["parent"] == "International Humanitarian Intelligence"
    assert humanitarian["civilian_only"] is True
    assert humanitarian["international_reach_claim"] is False
    assert humanitarian["map_intelligence_bound"] is True
    assert humanitarian["maps"]["map_intelligence_bound"] is True
    assert umbrella["name"] == "International Humanitarian Intelligence"
    assert umbrella["section_count"] == 8
    assert status["humanitarian_parent"] == "International Humanitarian Intelligence"
    assert status["intelligence_world_count_added"] == 0
