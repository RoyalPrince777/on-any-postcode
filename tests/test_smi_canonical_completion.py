from __future__ import annotations

from mission_control import (
    ai_behaviour_protocol,
    autonomy_levels,
    intelligence_lenses,
    smi_chat_grounded,
    smi_completion_contract,
    war_room_simulation_actions,
)


def test_smi_uses_one_canonical_a1_to_a7_operating_ladder(monkeypatch):
    monkeypatch.delenv("OAP_AUTONOMY_LEVEL", raising=False)

    assert tuple(autonomy_levels.AUTONOMY_LEVELS) == (
        "A1",
        "A2",
        "A3",
        "A4",
        "A5",
        "A6",
        "A7",
    )
    status = autonomy_levels.status()
    assert status["configured_level"] == "A3"
    assert status["a5_enabled"] is False
    assert status["a6_enabled"] is False
    assert status["a7_enabled"] is False
    assert status["authority_moves_with_level"] is False


def test_legacy_a0_fails_closed_into_canonical_a1(monkeypatch):
    monkeypatch.setenv("OAP_AUTONOMY_LEVEL", "A0")
    assert autonomy_levels.configured_level() == "A1"


def test_a7_is_constitutionally_locked_behind_external_proof():
    requirements = " | ".join(autonomy_levels.A7_REQUIREMENTS).lower()

    assert "external audit" in requirements
    assert "legal and compliance proof" in requirements
    assert "emergency halt proof" in requirements
    assert "public/private boundary proof" in requirements
    assert "constitutional review" in requirements


def test_completion_contract_reports_code_separately_from_runtime_proof():
    status = smi_completion_contract.completion_status()

    assert status["operating_level_model"] == "A1-A7"
    assert status["one_brain"] is True
    assert status["intelligence"]["lens_count"] == 26
    assert status["intelligence"]["core_lens_count"] == 10
    assert status["intelligence"]["execution_granted_by_lens"] is False
    assert status["green_gate"]["code_boundary_ready"] is True
    assert status["green_gate"]["smi_runtime_full_green"] is False
    assert status["truth_light"]["whole_smi_runtime"] == "not_full_green"

    missing = {item["id"] for item in status["missing_proof_gates"]}
    assert missing == {
        "founder_chat_interaction",
        "hrm_receipt_chain",
        "green_gate_aggregation",
        "rollback_recovery",
        "observability",
        "a7_external",
    }


def test_all_26_intelligence_lenses_remain_capabilities_not_execution_authority():
    assert len(intelligence_lenses.FULL_LENS_IDS) == 26
    assert len(intelligence_lenses.CORE_LENS_IDS) == 10

    routed = intelligence_lenses.public_route("Full Intelligence on SIKA")
    assert routed["active"] is True
    assert routed["mode"] == "full"
    assert len(routed["lenses"]) == 26
    assert routed["execution_granted"] is False
    assert routed["human_authority_final"] is True


def test_personal_smi_grounding_exposes_a5_a6_a7_as_locked_not_authority():
    text = smi_chat_grounded.evidence_contract(
        {
            "status": "degraded",
            "checks": {"audit": True, "approval_receipt": False},
            "invariants": {"execution_locked": True},
        }
    ).lower()

    assert '"a5_enabled":false' in text
    assert '"a6_enabled":false' in text
    assert '"a7_enabled":false' in text
    assert '"intelligence_lens_count":26' in text
    assert "higher levels never move human authority" in text
    assert "truth intelligence plus evidence intelligence" in text


def test_war_room_uses_learning_intelligence_and_keeps_old_action_as_quiet_alias():
    catalogue = war_room_simulation_actions.list_actions()
    ids = {item["id"] for item in catalogue["actions"]}

    assert "smi_learning_readiness_simulation" in ids
    assert "aci_readiness_simulation" not in ids
    assert catalogue["canonical_autonomy_ladder"] == "A1-A7"
    assert catalogue["global_locks"]["a5_enabled"] is False
    assert catalogue["global_locks"]["a6_enabled"] is False
    assert catalogue["global_locks"]["a7_enabled"] is False

    old = war_room_simulation_actions.simulate("aci_readiness_simulation", "SMI")
    assert old["action"]["id"] == "smi_learning_readiness_simulation"
    assert old["result"]["safe_to_execute"] is False


def test_behaviour_protocol_uses_a_level_locks_and_truth_evidence_green_rule():
    status = ai_behaviour_protocol.status()

    assert status["canonical_autonomy_ladder"] == "A1-A7"
    assert status["hard_locks"]["a5_enabled"] is False
    assert status["hard_locks"]["a6_enabled"] is False
    assert status["hard_locks"]["a7_enabled"] is False
    assert status["truth_light_rule"] == (
        "Only Truth Intelligence plus Evidence Intelligence can support a green claim."
    )
    assert status["overall_green"] is False
