from mission_control import live_brain, smi_capabilities
from oap.smi.command_intelligence import CommandIntelligence


def test_command_intelligence_is_six_bounded_capabilities_not_six_brains():
    status = CommandIntelligence().status()
    assert status["ready"] is True
    assert status["brain_count"] == 0
    assert status["stage_count"] == 6
    assert status["command_path"] == ("sgi", "tgi", "ogi", "dgi", "pgi", "rgi")
    assert status["independent_execute"] is False
    assert status["independent_approval"] is False
    assert status["prediction_claims_fact"] is False
    assert status["fail_closed_resilience"] is True
    assert status["human_authority_final"] is True


def test_command_review_preserves_war_room_judgement_and_human_boundary():
    review = CommandIntelligence().review(
        "The route engine failed after deploy; diagnose it before expanding globally.",
        "TECHNICAL",
        {
            "domains": ("Matrix Intelligence", "Movement Intelligence", "Earth Intelligence"),
        },
        high_impact=True,
    )
    stages = {stage["id"]: stage for stage in review["stages"]}
    assert review["command_path"] == ("sgi", "tgi", "ogi", "dgi", "pgi", "rgi")
    assert review["human_review_required"] is True
    assert review["war_room_next"] is True
    assert review["judgement_next"] is True
    assert review["guardian_boundary_preserved"] is True
    assert review["execution_authority"] is False
    assert review["approval_authority"] is False
    assert review["human_authority_final"] is True
    assert stages["dgi"]["triggered"] is True
    assert stages["pgi"]["prediction_is_fact"] is False
    assert "fail-closed" in stages["rgi"]["advice"]


def test_command_review_does_not_invent_failure_when_none_is_observed():
    review = CommandIntelligence().review(
        "Plan the next bounded OAP Maps proof in Mitcham.",
        "STRATEGY",
        {"domains": ("Movement Intelligence", "Earth Intelligence")},
    )
    stages = {stage["id"]: stage for stage in review["stages"]}
    assert stages["dgi"]["triggered"] is False
    assert review["high_impact"] is False
    assert review["human_review_required"] is False


def test_smi_registry_keeps_seven_worlds_and_registers_command_chain():
    validation = smi_capabilities.validate_smi_capabilities()
    status = smi_capabilities.smi_capability_status()
    assert validation["passed"] is True
    assert validation["checks"]["intelligence_worlds"] == 7
    assert validation["checks"]["brain_count_added_by_command_intelligence"] == 0
    assert validation["checks"]["command_stages"] == 6
    assert status["command_intelligence"]["command_path"] == (
        "sgi",
        "tgi",
        "ogi",
        "dgi",
        "pgi",
        "rgi",
    )
    assert status["human_authority_final"] is True
    assert status["independent_execution"] is False


def test_live_smi_brain_exposes_agi_and_command_chain_without_execution_authority():
    result = live_brain.review(
        request_id="live-command-v1",
        identity_id="00000000-0000-0000-0000-000000000009",
        content="Plan the next bounded OAP Maps proof in Mitcham.",
        history=[],
        image_attached=False,
    )
    assert result["agi_route"]["execution_authority"] is False
    assert result["command_intelligence"]["command_path"] == [
        "sgi",
        "tgi",
        "ogi",
        "dgi",
        "pgi",
        "rgi",
    ]
    assert result["command_intelligence"]["decision_authority"] is False
    assert result["command_intelligence"]["execution_authority"] is False
    assert "AGI_ROUTED" in result["processing_states"]
    assert "COMMAND_INTELLIGENCE_REVIEWED" in result["processing_states"]
    assert result["can_execute"] is False
    assert result["human_authority_final"] is True
