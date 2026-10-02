import pytest

from mission_control import sika_payment_submission_evidence


def test_schema_enforces_provider_idempotency_pair():
    sql = "\n".join(sika_payment_submission_evidence.SCHEMA_STATEMENTS)
    assert "UNIQUE(provider_id,idempotency_key)" in sql
    assert "'ACCEPTED','REJECTED','UNCERTAIN'" in sql


def test_accepted_submission_requires_provider_reference():
    with pytest.raises(
        sika_payment_submission_evidence.SubmissionEvidenceError,
        match="provider_reference_required_for_accepted_submission",
    ):
        sika_payment_submission_evidence.record(
            evidence_id="e-1",
            payment_id="p-1",
            idempotency_key="idem-1",
            provider_id="provider-1",
            provider_reference=None,
            outcome="ACCEPTED",
            evidence_hash="hash",
        )


def test_uncertain_outcome_never_allows_automatic_retry():
    evidence = sika_payment_submission_evidence.SubmissionEvidence(
        evidence_id="e-1",
        payment_id="p-1",
        idempotency_key="idem-1",
        provider_id="provider-1",
        provider_reference=None,
        outcome="UNCERTAIN",
        evidence_hash="hash",
    )
    assert evidence.human_review_required is True
    assert evidence.automatic_retry_allowed is False


def test_status_keeps_submission_evidence_non_executing():
    status = sika_payment_submission_evidence.status()
    assert status["provider_idempotency_replay_protection"] is True
    assert status["uncertain_outcome_state"] is True
    assert status["automatic_retry"] is False
    assert status["provider_calling"] is False
    assert status["payment_state_mutation"] is False
    assert status["money_movement"] is False
