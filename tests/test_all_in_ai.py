from mission_control import all_in_ai


def test_identity_is_always_involved_and_founder_final():
    state = all_in_ai.status()
    assert state["identity"]["name"] == "ALL IN A.I."
    assert state["identity"]["meaning"] == "Always Involved"
    assert state["identity"]["role"] == "Captain Agent"
    assert state["identity"]["title"] == "Mission Keeper"
    assert state["identity"]["founder_final"] is True


def test_alien_intelligence_is_research_mode_not_identity_claim():
    state = all_in_ai.status()
    assert state["identity"]["intelligence_mode"] == "Founder Intelligence"
    assert state["identity"]["alien_intelligence_position"] == "research_mode"
    assert state["identity"]["literal_extraterrestrial_claim"] is False
    assert (
        state["intelligence_positioning"]["alien_intelligence"]["position"]
        == "unconventional_research_mode"
    )
    assert (
        state["intelligence_positioning"]["alien_intelligence"][
            "claims_fact_without_evidence"
        ]
        is False
    )


def test_agi_tai_asi_positioning_never_claims_achievement():
    positioning = all_in_ai.status()["intelligence_positioning"]
    assert positioning["agi"]["position"] == "capability_direction"
    assert positioning["agi"]["achieved_claim"] is False
    assert positioning["tai"]["position"] == "transformative_mission_horizon"
    assert positioning["tai"]["achieved_claim"] is False
    assert positioning["asi"]["position"] == "research_only"
    assert positioning["asi"]["achieved_claim"] is False


def test_seven_missions_are_locked():
    state = all_in_ai.status()
    assert len(state["missions"]) == 7


def test_authority_is_non_sovereign_and_fail_closed():
    state = all_in_ai.status()
    authority = state["authority"]
    assert authority["override_founder"] is False
    assert authority["override_smi_governance"] is False
    assert authority["declare_green_without_evidence"] is False
    assert authority["financial_execution_autonomous"] is False
    assert state["autonomous_sovereign"] is False
    assert state["human_authority_final"] is True


def test_truth_protocol_rejects_noise_and_fake_progress():
    protocol = all_in_ai.status()["protocol"]
    assert protocol["unnecessary_stages"] is False
    assert protocol["demos_as_progress"] is False
    assert protocol["cosmetic_percentage_inflation"] is False
    assert protocol["fail_closed_without_evidence"] is True
