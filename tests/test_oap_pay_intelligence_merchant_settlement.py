from decimal import Decimal

from mission_control import (
    oap_pay_intelligence,
    sika_double_entry,
    sika_payment_disputes,
    sika_payment_orchestrator,
    sika_payment_submission_evidence,
)


def _intent(status="SETTLED"):
    return sika_payment_orchestrator.PaymentIntent(
        payment_id="pay-merchant-1",
        idempotency_key="idem-merchant-1",
        payer_account_id="acct-1",
        payee_reference="merchant-1",
        amount=Decimal("25.00"),
        currency="GBP",
        jurisdiction="United Kingdom",
        status=status,
        provider_reference="provider-ref-1",
    )


def _submission(outcome="ACCEPTED"):
    return sika_payment_submission_evidence.SubmissionEvidence(
        evidence_id="evidence-1",
        payment_id="pay-merchant-1",
        idempotency_key="idem-merchant-1",
        provider_id="provider-1",
        provider_reference="provider-ref-1" if outcome == "ACCEPTED" else None,
        outcome=outcome,
        evidence_hash="a" * 64,
    )


def test_merchant_intelligence_requires_certified_merchant_for_acceptance_advice():
    merchant = oap_pay_intelligence.merchant_intelligence(
        {
            "merchant_reference": "merchant-1",
            "checkout_reference": "checkout-1",
            "certified": True,
        }
    )
    assert merchant["valid"] is True
    assert merchant["payment_acceptance_advised"] is True
    assert merchant["execution_granted"] is False

    uncertified = oap_pay_intelligence.merchant_intelligence(
        {
            "merchant_reference": "merchant-1",
            "checkout_reference": "checkout-1",
            "certified": False,
        }
    )
    assert uncertified["payment_acceptance_advised"] is False


def test_activity_intelligence_builds_evidence_timeline():
    dispute = sika_payment_disputes.DisputeCase(
        dispute_id="dispute-1",
        payment_id="pay-merchant-1",
        reason_code="not_received",
        status="OPEN",
    )
    result = oap_pay_intelligence.activity_intelligence(
        payment_intent=_intent("SUBMITTED"),
        submission_evidence=_submission(),
        dispute=dispute,
    )
    assert result["valid"] is True
    assert result["timeline"] == ("SUBMITTED", "PROVIDER_ACCEPTED", "DISPUTE_OPEN")
    assert result["provider_submission_proven"] is True
    assert result["dispute_open"] is True
    assert result["money_movement"] is False


def test_settlement_intelligence_needs_settled_state_submission_and_balanced_journal():
    batch = sika_double_entry.validate_batch(
        journal_id="journal-1",
        reference="pay-merchant-1",
        lines=[
            sika_double_entry.line(
                account_id="payer",
                side="debit",
                amount="25.00",
                currency="GBP",
            ),
            sika_double_entry.line(
                account_id="merchant",
                side="credit",
                amount="25.00",
                currency="GBP",
            ),
        ],
    )
    result = oap_pay_intelligence.settlement_intelligence(
        payment_intent=_intent("SETTLED"),
        submission_evidence=_submission(),
        journal_batch=batch,
    )
    assert result["valid"] is True
    assert result["provider_submission_proven"] is True
    assert result["journal_present"] is True
    assert result["journal_balanced"] is True
    assert result["settlement_proven"] is True
    assert result["external_money_movement_proven"] is False


def test_settlement_intelligence_refuses_payment_mismatch():
    evidence = sika_payment_submission_evidence.SubmissionEvidence(
        evidence_id="evidence-other",
        payment_id="pay-other",
        idempotency_key="idem-other",
        provider_id="provider-1",
        provider_reference="provider-ref-other",
        outcome="ACCEPTED",
        evidence_hash="b" * 64,
    )
    result = oap_pay_intelligence.settlement_intelligence(
        payment_intent=_intent("SETTLED"),
        submission_evidence=evidence,
        journal_batch=None,
    )
    assert result["settlement_proven"] is False
    assert result["provider_submission_proven"] is False


def test_status_marks_only_implemented_intelligence_green():
    status = oap_pay_intelligence.status()
    assert status["merchant_intelligence"] is True
    assert status["settlement_intelligence"] is True
    assert status["activity_intelligence"] is True
    assert status["fraud_intelligence"] is False
    assert status["guardian_intelligence"] is False
