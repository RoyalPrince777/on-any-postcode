from mission_control import smi_auto_review


def test_named_agent_invocation_routes_exact_canonical_lenses():
    roles = smi_auto_review.explicit_roles(
        "Shere Khan do the Claw Test, then Neo and Owl review it."
    )
    assert roles == ("Neo", "Shere Khan", "Owl")


def test_auto_mode_uses_stable_review_pack_when_no_name_was_requested():
    roles = smi_auto_review.selected_roles("SMI review this", auto_mode=True)
    assert roles == (
        "Neo",
        "Shere Khan",
        "Bagheera",
        "Agent Smith",
        "Owl",
        "Guardian",
        "Green Gate",
    )


def test_explicit_name_beats_default_auto_pack():
    roles = smi_auto_review.selected_roles("Bagheera review this", auto_mode=True)
    assert roles == ("Bagheera",)


def test_vote_board_is_evidence_classification_not_personality_simulation():
    board = smi_auto_review.build_vote_board(
        roles=("Neo", "Shere Khan", "Guardian"),
        brain={"passed": True, "high_impact": False},
        coherence={"passed": True},
        judgement={"constitution_consistent": True},
        guardian_outcome="PASSED",
    )
    assert board["summary"] == {"PASS": 3, "FAIL": 0, "CONDITIONAL": 0}
    assert board["authority_granted"] is False
    assert all(item["deterministic_evidence_review"] for item in board["votes"])
    assert not any(item["independent_personality_claimed"] for item in board["votes"])
