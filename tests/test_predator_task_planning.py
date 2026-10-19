"""Predator task proposal contracts: no agent execution or authority."""
from oap.smi.predator_task_planning import ACTIVE_CANDIDATES, propose_task


def test_four_candidates_have_bounded_proposals():
    assert ACTIVE_CANDIDATES == {"dek", "thia", "bud", "kwei"}
    for candidate in ACTIVE_CANDIDATES:
        proposal = propose_task(candidate, "Assess recovery", {"log": "supplied"})
        assert proposal.decision == "HUMAN_REVIEW"
        assert proposal.lifecycle_direction == "LEARN"


def test_unknown_and_advisory_roles_cannot_propose():
    for candidate in ("tessa", "njohrr", "unknown"):
        assert propose_task(candidate, "Assess recovery", {"log": "supplied"}).decision == "DENY"


def test_missing_task_or_evidence_denied():
    assert propose_task("dek", "", {"log": "supplied"}).decision == "DENY"
    assert propose_task("dek", "Assess recovery", None).decision == "DENY"
    assert propose_task("dek", "Assess recovery", {"log": ""}).decision == "DENY"
    assert propose_task("dek", "Assess recovery", {"": "supplied"}).decision == "DENY"
