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
