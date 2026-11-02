from __future__ import annotations

import app as app_module
from mission_control import smi_auto
from smi_gateway import app as smi_gateway_app


def test_smi_auto_is_low_noise_and_never_executes():
    observed = smi_auto.observe("GET", "/the-spot/maps-weather-travel")

    assert observed["active"] is True
    assert observed["light"] == "purple"
    assert observed["provider_call_performed"] is False
    assert observed["database_write_performed"] is False
    assert observed["execution_granted"] is False
    assert observed["approval_granted"] is False
    assert observed["human_authority_final"] is True
    assert "truth" in observed["lenses"]
    assert "evidence" in observed["lenses"]
    assert "alignment" in observed["lenses"]


def test_smi_auto_escalates_writes_without_approving_them():
    observed = smi_auto.observe("POST", "/mission/judgement")

    assert observed["write_action"] is True
    assert observed["war_room_escalation"] is True
    assert "risk" in observed["lenses"]
    assert "decision" in observed["lenses"]
    assert "judgement" in observed["lenses"]
    assert observed["execution_granted"] is False
    assert observed["approval_granted"] is False


def test_oap_app_responses_expose_safe_smi_auto_headers(client):
    response = client.get("/the-spot")

    assert response.headers["X-OAP-SMI-Auto"] == "active"
    assert response.headers["X-OAP-SMI-Mode"] == "automatic_low_noise"
    assert response.headers["X-OAP-SMI-Execution"] == "blocked"


def test_smi_origin_enters_through_founder_sign_in_then_private_aliases():
    gateway = smi_gateway_app.test_client()

    assert gateway.get("/").headers["Location"] == "/auth?next=/mission/ollama"
    assert gateway.get("/smi").headers["Location"] == "/mission/ollama"
    assert gateway.get("/chat").headers["Location"] == "/mission/ollama"
    assert gateway.get("/war-room").headers["Location"] == "/mission/war-room"


def test_public_status_declares_same_non_authority_contract():
    snapshot = smi_auto.public_status()

    assert snapshot["active"] is True
    assert snapshot["mode"] == "automatic_low_noise"
    assert snapshot["provider_call_per_request"] is False
    assert snapshot["database_write_per_request"] is False
    assert snapshot["execution_granted"] is False
    assert snapshot["approval_granted"] is False
    assert snapshot["human_authority_final"] is True


def test_app_registers_smi_auto_response_hook():
    names = {func.__name__ for func in app_module.app.after_request_funcs[None]}
    assert "_oap_smi_auto_response" in names


def test_smi_auto_adds_only_mission_relevant_semantic_lenses():
    observed = smi_auto.observe(
        "GET",
        "/mission/ollama",
        message="Why is Link Up confusing users on mobile?",
    )
    assert observed["selector"] == "surface+action+mission"
    assert set(observed["semantic_lenses"]) == {"ux", "behaviour"}
    assert "competitive" not in observed["lenses"]
    assert "trend" not in observed["lenses"]


def test_smi_auto_combines_surface_action_and_mission_without_all_intelligence():
    observed = smi_auto.observe(
        "POST",
        "/mission/release",
        message="Check whether this release is ready and how rollback works if it fails.",
    )
    assert {"readiness", "gap", "resilience", "risk"}.issubset(set(observed["semantic_lenses"]))
    assert observed["write_action"] is True
    assert observed["war_room_escalation"] is True
    assert len(observed["lenses"]) < 28
    assert observed["execution_granted"] is False
    assert observed["approval_granted"] is False


def test_smi_auto_without_message_preserves_existing_low_noise_contract():
    observed = smi_auto.observe("GET", "/the-spot")
    assert observed["semantic_lenses"] == ()
    assert observed["lenses"] == smi_auto.BASE_LENSES


def test_smi_intelligence_selects_minimum_sufficient_a1_to_a7_level():
    base = smi_auto.observe("GET", "/the-spot")
    semantic = smi_auto.observe(
        "GET",
        "/mission/ollama",
        message="Why is this navigation confusing on mobile?",
    )
    consequential = smi_auto.observe(
        "POST",
        "/mission/release",
        message="Verify release readiness, dependencies, rollback and recovery before approval.",
    )

    assert base["smi_intelligence"]["level"] == "A1"
    assert semantic["smi_intelligence"]["level"] in {"A3", "A4"}
    assert consequential["smi_intelligence"]["level"] in {"A6", "A7"}
    assert base["smi_intelligence"]["stop"] is True
    assert consequential["execution_granted"] is False
    assert consequential["approval_granted"] is False


def test_smi_intelligence_does_not_escalate_depth_without_need():
    observed = smi_auto.observe("GET", "/the-spot", message="Hello")
    assert observed["smi_intelligence"]["level"] == "A1"
    assert observed["semantic_lenses"] == ()
    assert observed["smi_intelligence"]["stop_reason"].startswith("minimum sufficient intelligence")


def test_nirmata_and_aei_route_as_advisory_lenses_only():
    for phrase, expected in (("Nirmata design upgrade", "architecture"), ("AEI execute upgrade", "security")):
        result = smi_auto.observe("GET", "/mission/smi", message=phrase)
        assert expected in result["semantic_lenses"]
        assert result["execution_granted"] is False
        assert result["approval_granted"] is False
        assert result["provider_call_performed"] is False
        assert result["database_write_performed"] is False
        assert result["human_authority_final"] is True


def test_hathi_memory_learning_routes_to_canonical_jungle_passport_with_seven_thinking():
    result = smi_auto.observe("GET", "/mission/smi", message="Memory and learning review")
    mission = result["specialist_mission"]
    assert mission["lead"] == "Colonel Hathi"
    assert mission["lead_alias"] == "Hathi"
    assert mission["lead_passport"] == "JUNGLE-HATHI-001"
    assert mission["support"] == ("Hathi Jr", "Owl", "Oracle", "Fox")
    assert mission["thinking_depth"] == 7
    assert len(mission["selected_checks"]) == 7
    assert {x["block"] for x in mission["selected_checks"]} == {"Mind"}
    assert set(mission["lenses"]).issubset(set(result["lenses"]))
    assert mission["memory_owner"] == "HRM Core"
    assert mission["guardian_required"] and mission["green_gate_required"]
    assert not mission["checks_executed"] and not mission["receipts_verified"]
    assert not mission["independent_votes_proven"]
    assert not mission["execution_granted"] and not mission["approval_granted"]
    assert mission["human_authority_final"]
    assert not result["provider_call_performed"]
    assert not result["database_write_performed"]


def test_non_memory_request_does_not_invoke_hathi_specialist_team():
    assert smi_auto.observe("GET", "/the-spot", message="Hello")["specialist_mission"] is None


def test_dynamic_multi_division_routing_preserves_one_brain_and_governance():
    selection = smi_auto.route_divisions(("truth", "engineering", "memory", "engineering"), thinking="7")
    assert tuple(row["division"] for row in selection["divisions"]) == ("truth", "engineering", "memory")
    assert selection["thinking_depth"] == 7
    assert len(selection["selected_checks"]) == 7
    assert selection["divisions"][-1]["lead"] == "Colonel Hathi"
    assert selection["selection_only"] is True
    assert selection["agents_executed"] is False
    assert selection["independent_votes_proven"] is False
    assert selection["guardian_required"] is True
    assert selection["green_gate_required"] is True
    assert selection["hrm_proof_required"] is True
    assert selection["execution_granted"] is False
    assert selection["approval_granted"] is False
    assert selection["human_authority_final"] is True


def test_dynamic_multi_division_auto_escalates_and_rejects_invalid_scope():
    import pytest
    full = smi_auto.route_divisions(("truth", "strategy", "engineering", "decision", "memory"))
    assert full["thinking_depth"] == 21
    assert len(full["selected_checks"]) == 21
    assert len(full["divisions"]) == 5
    assert smi_auto.route_divisions(("truth",), thinking="AUTO")["thinking_depth"] == 3
    for divisions, thinking in (((), "AUTO"), (("unknown",), "AUTO"), (("truth",), "14")):
        with pytest.raises(ValueError):
            smi_auto.route_divisions(divisions, thinking=thinking)


def test_memory_auto_depth_matches_hathi_seven_check_contract():
    memory_only = smi_auto.route_divisions(("memory",), thinking="AUTO")
    engineering_and_memory = smi_auto.route_divisions(("engineering", "memory"), thinking="AUTO")
    for selection in (memory_only, engineering_and_memory):
        assert selection["thinking_depth"] == 7
        assert len(selection["selected_checks"]) == 7
        assert selection["selection_only"] is True
        assert selection["agents_executed"] is False
        assert selection["execution_granted"] is False
        assert selection["approval_granted"] is False
        assert selection["human_authority_final"] is True
    assert smi_auto.route_divisions(("engineering",), thinking="AUTO")["thinking_depth"] == 3
