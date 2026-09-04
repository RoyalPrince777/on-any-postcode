from mission_control import smi_capabilities
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
