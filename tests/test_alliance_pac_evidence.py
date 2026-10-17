"""Contract tests for fail-closed PAC evidence gates."""
from mission_control.alliance_pac_evidence import evaluate_pac_evidence
from oap.war_room.agent_selection import SCORE_WEIGHTS


def test_missing_evidence_never_becomes_zero_performance():
    result = evaluate_pac_evidence({}, {}, is_registered=True, independent_review=True)
    assert result["status"] == "NOT_RATED"
    assert result["score"] is None


def test_unregistered_or_self_review_cannot_rank():
    metrics = {k: 90 for k in SCORE_WEIGHTS}
    evidence = {k: "receipt-123" for k in SCORE_WEIGHTS}
    assert evaluate_pac_evidence(metrics, evidence, is_registered=False,
                                 independent_review=True)["score"] is None
    assert evaluate_pac_evidence(metrics, evidence, is_registered=True,
                                 independent_review=False)["score"] is None


def test_invalid_metric_rejected():
    metrics = {k: 90 for k in SCORE_WEIGHTS}
    metrics["task_fit"] = 900
    evidence = {k: "receipt-123" for k in SCORE_WEIGHTS}
    result = evaluate_pac_evidence(metrics, evidence, is_registered=True,
                                   independent_review=True)
    assert result["status"] == "INVALID"


def test_complete_evidence_is_advisory_only():
    metrics = {k: 90 for k in SCORE_WEIGHTS}
    evidence = {k: "receipt-123" for k in SCORE_WEIGHTS}
    result = evaluate_pac_evidence(metrics, evidence, is_registered=True,
                                   independent_review=True)
    assert result["status"] == "EVIDENCE_SUBMITTED"
    assert result["authority_effect"] == "none"
    assert result["score"] == 90.0
