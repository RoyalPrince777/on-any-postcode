from oap.smi import independent_oversight


def _all_true():
    return {dimension: True for dimension in independent_oversight.OVERSIGHT_DIMENSIONS}


def test_status_keeps_level_07_read_only_and_human_final():
    state = independent_oversight.status()
    assert state["observation_ladder_level"] == 7
    assert state["independent_execution"] is False
    assert state["independent_approval"] is False
    assert state["production_write"] is False
    assert state["self_certification_allowed"] is False
    assert state["human_authority_final"] is True


def test_review_requires_all_seven_dimensions_and_proven_evidence_for_green():
    evidence = _all_true()
    evidence["evidence_state"] = "proven"
    result = independent_oversight.review(evidence)
    assert result["green_candidate"] is True
    assert result["signal"] == "green"
    assert result["blocking_dimensions"] == ()
    assert result["unresolved_dimensions"] == ()
    assert result["execution_granted"] is False
    assert result["approval_granted"] is False


def test_false_dimension_blocks_and_cannot_grant_authority():
    evidence = _all_true()
    evidence["privacy"] = False
    evidence["evidence_state"] = "proven"
    result = independent_oversight.review(evidence)
    assert result["green_candidate"] is False
    assert result["signal"] == "red"
    assert "privacy" in result["blocking_dimensions"]
    assert result["execution_granted"] is False
    assert result["approval_granted"] is False
    assert result["human_authority_final"] is True


def test_missing_or_non_boolean_evidence_stays_unresolved_not_green():
    evidence = _all_true()
    del evidence["reversibility"]
    evidence["bias"] = "probably"
    evidence["evidence_state"] = "stale"
    result = independent_oversight.review(evidence)
    assert result["green_candidate"] is False
    assert result["signal"] == "yellow"
    assert "bias" in result["unresolved_dimensions"]
    assert "reversibility" in result["unresolved_dimensions"]
    assert "evidence_state" in result["unresolved_dimensions"]