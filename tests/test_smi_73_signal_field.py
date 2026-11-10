from mission_control import smi_73_signal_field as field


def test_definition_has_locked_7_14_21_73_777_architecture():
    status = field.definition_status()
    assert status["signal_count"] == 73
    assert status["major_dimension_count"] == 21
    assert status["star_gate_count"] == 7
    assert status["reviewer_count"] == 14
    assert status["numeric_architecture"] == ("7", "14", "21", "73", "777")
    assert status["upgrade_only"] is True
    assert status["no_cosmetic_progress"] is True


def test_unknown_evidence_never_claims_green():
    result = field.evaluate()
    assert result["signal_count"] == 73
    assert result["green_100"] is False
    assert result["completion_percentage"] == 0
    assert result["seal_777"] == "not_earned"
    assert result["counts"]["unknown"] == 73
    assert result["star_summary"] == {"earned": 0, "total": 7}


def test_all_required_evidence_proven_earns_green_and_seal():
    evidence = {key: "proven" for key in field.SIGNAL_KEYS}
    result = field.evaluate(evidence)
    assert result["green_100"] is True
    assert result["completion_percentage"] == 100
    assert result["seal_777"] == "earned"
    assert result["counts"]["proven"] == 73
    assert result["star_summary"] == {"earned": 7, "total": 7}


def test_blocked_signal_prevents_green_and_cannot_be_averaged_away():
    evidence = {key: "proven" for key in field.SIGNAL_KEYS}
    evidence["crown.end_to_end_proof"] = "blocked"
    result = field.evaluate(evidence)
    assert result["green_100"] is False
    assert result["completion_percentage"] < 100
    assert result["seal_777"] == "not_earned"
    assert any(
        item["name"] == "end_to_end" and item["state"] == "blocked"
        for item in result["stars"]
    )


def test_matrix_votes_are_deterministic_evidence_reviews_not_simulated_opinions():
    result = field.evaluate()
    assert len(result["votes"]) == 14
    assert all(item["deterministic_evidence_review"] for item in result["votes"])
    assert all(not item["fictional_opinion_claimed"] for item in result["votes"])
    assert result["review"]["simulation_is_completion"] is False


def test_single_smi_adversarial_review_is_evidence_only():
    review = field.evaluate()["adversarial_review"]
    assert review["mode"] == "single_smi_evidence_review"
    assert review["separate_agents_created"] is False
    assert review["new_vote_engine_created"] is False
    assert review["human_authority_final"] is True
    assert review["truth_mode"]["proven_count"] == 0
    assert review["truth_mode"]["required_count"] == 73
    assert review["truth_mode"]["unknown_count"] == 73
    assert review["red_team"]["hold_green"] is True
    assert review["devils_advocate"]["score_is_release_certification"] is False
    assert review["devils_advocate"]["test_pass_is_target_runtime_proof"] is False


def test_red_team_exposes_mandatory_failure_despite_high_signal_score():
    evidence = {key: "proven" for key in field.SIGNAL_KEYS}
    evidence["crown.recovery_proof"] = "blocked"
    result = field.evaluate(evidence)
    review = result["adversarial_review"]
    assert result["green_100"] is False
    assert review["red_team"]["hold_green"] is True
    assert "crown.recovery_proof" in review["red_team"]["blocked_signals"]
    assert {"signal": "crown.recovery_proof", "state": "blocked"} in review["red_team"]["mandatory_unresolved"]
    assert review["truth_mode"]["proven_count"] == 72


def test_all_claimed_proven_does_not_imply_live_certification():
    evidence = {key: "proven" for key in field.SIGNAL_KEYS}
    result = field.evaluate(evidence)
    review = result["adversarial_review"]
    assert review["red_team"]["hold_green"] is False
    assert review["devils_advocate"]["score_is_release_certification"] is False
    assert review["devils_advocate"]["test_pass_is_target_runtime_proof"] is False
