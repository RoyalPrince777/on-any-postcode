from mission_control import ai_behaviour, autonomy_levels, smi_chat_grounded


def test_adaptive_reasoning_depth_is_exactly_3_7_21():
    status = ai_behaviour.status()
    assert status["adaptive_reasoning_depths"] == (3, 7, 21)
    assert ai_behaviour.depth_for("simple") == 3
    assert ai_behaviour.depth_for("complex") == 7
    assert ai_behaviour.depth_for("war_room") == 21


def test_response_behaviour_is_answer_first_and_does_not_repeat_identity_prefix():
    status = ai_behaviour.status()
    assert status["answer_first"] is True
    assert status["concise_by_default"] is True
    assert status["repeated_smi_prefix_allowed"] is False
    assert status["private_chain_of_thought_exposed"] is False
    assert status["safe_process_summary_allowed"] is True


def test_grounded_contract_exposes_a4_truth_without_granting_chat_execution(monkeypatch):
    monkeypatch.setenv("OAP_AUTONOMY_LEVEL", "A4")
    assert autonomy_levels.status()["a4_enabled"] is True
    contract = smi_chat_grounded.evidence_contract(
        {"status": "ok", "checks": {"runtime": True}, "invariants": {"execution_locked": True}}
    )
    assert '"autonomy_level":"A4"' in contract
    assert '"a4_enabled":true' in contract
    assert "A5 is locked" in contract
    assert "never grants chat permission to spend, deploy, dispatch, publish" in contract
    assert "adaptive private reasoning depth 3" in contract
    assert "Never reveal hidden chain-of-thought" in contract


def test_thinking_depth_uses_existing_mind_body_soul_checks_without_new_authority():
    for mode, expected in (("simple", 3), ("review", 7), ("war_room", 21)):
        result = ai_behaviour.review_checks_for(mode)
        assert result["thinking_depth"] == expected
        assert len(result["selected_checks"]) == expected
        assert result["total_available_checks"] == 21
        assert result["checks_executed"] is False
        assert result["checks_passed"] is False
        assert result["execution_granted"] is False
        assert result["approval_granted"] is False
        assert result["human_authority_final"] is True
    full = ai_behaviour.review_checks_for("war_room")
    assert {item["block"] for item in full["selected_checks"]} == {"Mind", "Body", "Soul"}
    assert full["selected_checks"][:7] == ai_behaviour.review_checks_for("review")["selected_checks"]


def test_existing_behaviour_status_exposes_real_3_7_21_check_profiles():
    profiles = ai_behaviour.status()["thinking_check_profiles"]
    assert tuple(profiles) == ("3", "7", "21")
    for depth in (3, 7, 21):
        profile = profiles[str(depth)]
        assert len(profile["selected_checks"]) == depth
        assert profile["checks_executed"] is False
        assert profile["execution_granted"] is False
