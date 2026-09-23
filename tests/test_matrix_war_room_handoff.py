from __future__ import annotations

import pytest

from mission_control import matrix_signal_bus, matrix_war_room, war_room


def consequential_signal():
    return matrix_signal_bus.route_signal(
        sender="Morpheus",
        topic="Possible false green",
        kind="truth_challenge",
        evidence=("CI link supplied, not independently verified",),
        consequential=True,
    )


def test_canonical_war_room_exposes_matrix_topology_without_promoting_candidates():
    result = war_room.get_war_room_dashboard()
    matrix = result["matrix_signal_bus"]
    assert matrix["registered_count"] == 7
    assert matrix["extended_review_count"] == 8
    assert matrix["full_green"] is False
    assert len(matrix["participants"]) == 15
    for item in matrix["participants"]:
        assert item["can_execute"] is False
        if item["status"] == "passport_review":
            assert item["can_emit_signal"] is False
    assert result["can_execute"] is False
    assert result["can_approve"] is False


def test_consequential_signal_handoff_is_not_a_vote_receipt_or_approval():
    signal = consequential_signal()
    pack = war_room.get_matrix_signal_war_room_review(signal)
    assert pack["sender"] == "Morpheus"
    assert pack["signal_id"] == signal["signal_id"]
    assert pack["evidence_claims"] == signal["evidence"]
    assert pack["evidence_verified"] is False
    assert pack["actual_agent_votes"] == ()
    assert pack["simulated_specialist_views"] == ()
    assert pack["registered_core_count"] == 7
    assert pack["extended_review_count"] == 8
    assert len(pack["candidate_review_roster"]) == 8
    assert pack["hrm_receipt_required"] is True
    assert pack["hrm_receipt_recorded"] is False
    assert pack["guardian_required"] is True
    assert pack["green_gate_required"] is True
    assert pack["founder_approved"] is False
    assert pack["execution_granted"] is False
    assert pack["external_action_taken"] is False
    assert pack["full_green"] is False


@pytest.mark.parametrize("sender", matrix_signal_bus.EXTENDED_REVIEW_ORDER)
def test_review_only_candidate_cannot_be_a_war_room_signal_sender(sender):
    signal = consequential_signal()
    signal["sender"] = sender
    with pytest.raises(ValueError, match="Registered Matrix sender required"):
        matrix_war_room.review_pack(signal)


@pytest.mark.parametrize(
    ("field", "unsafe"),
    [
        ("war_room_required", False),
        ("human_authority_required", False),
        ("human_authority_final", False),
        ("guardian_required", False),
        ("green_gate_required", False),
        ("hrm_receipt_required", False),
        ("execution_granted", True),
        ("external_action_taken", True),
        ("self_approval_allowed", True),
        ("permission_change_allowed", True),
        ("agent_creation_allowed", True),
        ("sender_channel", "invented_channel"),
        ("state", "approved"),
    ],
)
def test_invalid_or_authority_expanding_envelopes_fail_closed(field, unsafe):
    signal = consequential_signal()
    signal[field] = unsafe
    with pytest.raises(ValueError):
        matrix_war_room.review_pack(signal)


def test_nonconsequential_signal_is_not_fake_war_room_approval():
    signal = matrix_signal_bus.route_signal(sender="Neo", topic="Low impact observation")
    with pytest.raises(ValueError, match="Consequential"):
        matrix_war_room.review_pack(signal)


@pytest.mark.parametrize("evidence", [["ok", ""], "fake source", [None]])
def test_invalid_evidence_claim_shape_fails_closed(evidence):
    signal = consequential_signal()
    signal["evidence"] = evidence
    with pytest.raises(ValueError, match="evidence list"):
        matrix_war_room.review_pack(signal)
