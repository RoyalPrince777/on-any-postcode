from __future__ import annotations

from mission_control import live_brain, smi_capabilities
from oap.smi.command_intelligence import CommandIntelligence

EXPECTED_COMMAND_PATH = (
    "sgi",
    "tgi",
    "ogi",
    "dgi",
    "pgi",
    "rgi",
    "adgi",
    "mgi",
)
EXPECTED_CORE_PATH = ("agi", *EXPECTED_COMMAND_PATH)
EXPECTED_SUPPORT = ("cgi", "cogi", "egi", "lgi", "tegi", "regi")


def test_command_intelligence_is_9_core_plus_6_support_not_extra_brains():
    status = CommandIntelligence().status()
    assert status["ready"] is True
    assert status["brain_count"] == 0
    assert status["stage_count"] == 8
    assert status["command_path"] == EXPECTED_COMMAND_PATH
    assert status["core_path"] == EXPECTED_CORE_PATH
    assert status["core_general_intelligence_count"] == 9
    assert status["supporting_ids"] == EXPECTED_SUPPORT
    assert status["supporting_count"] == 6
    assert status["total_general_intelligence_capabilities"] == 15
    assert status["independent_execute"] is False
    assert status["independent_approval"] is False
    assert status["prediction_claims_fact"] is False
    assert status["fail_closed_resilience"] is True
    assert status["adaptive_mutates_approved_action"] is False
    assert status["meta_decision_authority"] is False
    assert status["human_authority_final"] is True


def test_command_review_preserves_war_room_judgement_and_human_boundary():
    review = CommandIntelligence().review(
        "The route engine failed after deploy; diagnose it before expanding globally.",
        "TECHNICAL",
        {
            "domains": (
                "Matrix Intelligence",
                "Movement Intelligence",
                "Earth Intelligence",
            ),
        },
        high_impact=True,
    )
    stages = {stage["id"]: stage for stage in review["stages"]}
    assert review["core_path"] == EXPECTED_CORE_PATH
    assert review["command_path"] == EXPECTED_COMMAND_PATH
    assert review["supporting_ids"] == EXPECTED_SUPPORT
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
    assert "never silently mutate" in stages["adgi"]["advice"]
    assert stages["mgi"]["decision_authority"] is False


def test_supporting_intelligences_are_advisory_and_not_in_command_path():
    review = CommandIntelligence().review(
        "Plan a resilient local-first release.",
        "STRATEGY",
        {"domains": ("Matrix Intelligence",)},
    )
    support = {item["id"]: item for item in review["supporting_intelligence"]}
    assert tuple(support) == EXPECTED_SUPPORT
    for item in support.values():
        assert item["advisory_only"] is True
        assert item["decision_authority"] is False
        assert item["execution_authority"] is False
    assert not set(EXPECTED_SUPPORT) & set(review["command_path"])


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


def test_smi_registry_keeps_seven_worlds_and_registers_9_plus_6_model():
    validation = smi_capabilities.validate_smi_capabilities()
    status = smi_capabilities.smi_capability_status()
    assert validation["passed"] is True
    assert validation["checks"]["intelligence_worlds"] == 7
    assert validation["checks"]["brain_count_added_by_command_intelligence"] == 0
    assert validation["checks"]["core_general_intelligence"] == 9
    assert validation["checks"]["command_stages"] == 8
    assert validation["checks"]["supporting_general_intelligence"] == 6
    assert validation["checks"]["total_general_intelligence_capabilities"] == 15
    assert status["command_intelligence"]["core_path"] == EXPECTED_CORE_PATH
    assert status["command_intelligence"]["supporting_ids"] == EXPECTED_SUPPORT
    assert status["core_general_intelligence_count"] == 9
    assert status["supporting_general_intelligence_count"] == 6
    assert status["human_authority_final"] is True
    assert status["independent_execution"] is False


def test_live_smi_brain_exposes_upgraded_command_chain_without_execution_authority():
    result = live_brain.review(
        request_id="live-command-v2",
        identity_id="00000000-0000-0000-0000-000000000009",
        content="Plan the next bounded OAP Maps proof in Mitcham.",
        history=[],
        image_attached=False,
    )
    assert result["agi_route"]["execution_authority"] is False
    assert result["command_intelligence"]["command_path"] == list(
        EXPECTED_COMMAND_PATH
    )
    assert result["command_intelligence"]["decision_authority"] is False
    assert result["command_intelligence"]["execution_authority"] is False
    assert "AGI_ROUTED" in result["processing_states"]
    assert "COMMAND_INTELLIGENCE_REVIEWED" in result["processing_states"]
    assert result["can_execute"] is False
    assert result["human_authority_final"] is True
