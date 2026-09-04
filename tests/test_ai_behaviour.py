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
