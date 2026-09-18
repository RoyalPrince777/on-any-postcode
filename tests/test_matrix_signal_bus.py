from __future__ import annotations

import pytest

from mission_control import matrix_signal_bus


def test_registered_matrix_team_stays_canonical_seven() -> None:
    assert matrix_signal_bus.registered_matrix_names() == (
        "Neo",
        "Morpheus",
        "Trinity",
        "Oracle",
        "Architect",
        "Keymaker",
        "Seraph",
    )


def test_extended_matrix_names_remain_passport_review() -> None:
    assert matrix_signal_bus.extended_review_names() == (
        "Tank",
        "Dozer",
        "Agent Smith",
        "Twinz",
        "Niobe",
        "Apoc",
    )
    projection = matrix_signal_bus.topology()
    extended = {
        item["name"]: item
        for item in projection["participants"]
        if item["name"] in matrix_signal_bus.EXTENDED_REVIEW_ORDER
    }
    assert all(item["status"] == "passport_review" for item in extended.values())
    assert all(item["can_emit_signal"] is False for item in extended.values())
    assert all(item["can_execute"] is False for item in extended.values())


def test_registered_agent_signal_routes_through_matrix_and_trinity() -> None:
    signal = matrix_signal_bus.route_signal(
        sender="Neo",
        topic="Primary route failed",
        kind="recovery",
        urgency="high",
        confidence=0.8,
        evidence=("route probe failed",),
        requested_action="review fallback",
    )

    assert signal["sender_channel"] == "recovery_and_anomaly"
    assert signal["delivery_path"][0] == "Neo"
    assert "Matrix System" in signal["delivery_path"]
    assert "Trinity" in signal["delivery_path"]
    assert "SMI" in signal["delivery_path"]
    assert signal["execution_granted"] is False
    assert signal["external_action_taken"] is False
    assert signal["self_approval_allowed"] is False


def test_passport_review_candidate_cannot_emit_live_signal() -> None:
    with pytest.raises(ValueError, match="not a registered Matrix agent"):
        matrix_signal_bus.route_signal(
            sender="Tank",
            topic="Coordinate operations",
        )


def test_unregistered_recipient_is_rejected() -> None:
    with pytest.raises(ValueError, match="Unknown or unregistered Matrix recipient"):
        matrix_signal_bus.route_signal(
            sender="Trinity",
            topic="Coordinate review",
            recipients=("Twinz",),
        )


def test_consequential_signal_requires_governance_path() -> None:
    signal = matrix_signal_bus.route_signal(
        sender="Morpheus",
        topic="Possible false green",
        kind="truth_challenge",
        consequential=True,
    )

    assert signal["guardian_required"] is True
    assert signal["green_gate_required"] is True
    assert signal["war_room_required"] is True
    assert signal["human_authority_required"] is True
    assert signal["human_authority_final"] is True
    assert signal["execution_granted"] is False


def test_topology_preserves_system_roles_and_no_full_green_claim() -> None:
    projection = matrix_signal_bus.topology()

    assert projection["coordinator"] == "Trinity"
    assert projection["interpreter"] == "SMI"
    assert projection["memory"] == "HRM Core"
    assert projection["protector"] == "Guardian"
    assert projection["proof_gate"] == "Green Gate"
    assert projection["consequential_review"] == "War Room"
    assert projection["final_authority"] == "Human Authority"
    assert projection["execution_granted"] is False
    assert projection["full_green"] is False


def test_niobe_and_apoc_are_review_only() -> None:
    projection = matrix_signal_bus.topology()
    participants = {item["name"]: item for item in projection["participants"]}
    for name in ("Niobe", "Apoc"):
        assert participants[name]["status"] == "passport_review"
        assert participants[name]["can_emit_signal"] is False
        assert participants[name]["can_execute"] is False
