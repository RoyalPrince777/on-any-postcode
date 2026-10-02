from decimal import Decimal

import pytest

from mission_control import (
    sika_double_entry,
    sika_payment_orchestrator,
    sika_refund_intent,
)


def _payment(status="SETTLED", amount=Decimal("100.00")):
    return sika_payment_orchestrator.PaymentIntent(
        payment_id="pay-1",
        idempotency_key="idem-pay-1",
        payer_account_id="acct-1",
        payee_reference="merchant-1",
        amount=amount,
        currency="GBP",
        jurisdiction="United Kingdom",
        status=status,
    )


def test_refund_requires_settled_original_payment():
    with pytest.raises(sika_refund_intent.RefundError, match="original_payment_not_settled"):
        sika_refund_intent.prepare(
            refund_id="refund-1",
            idempotency_key="refund-idem-1",
            original_payment=_payment(status="SUBMITTED"),
            amount="10",
            reason="customer_return",
        )


def test_refund_cannot_exceed_original_payment():
    with pytest.raises(sika_refund_intent.RefundError, match="refund_exceeds_original_payment"):
        sika_refund_intent.prepare(
            refund_id="refund-1",
            idempotency_key="refund-idem-1",
            original_payment=_payment(),
            amount="101",
            reason="customer_return",
        )


def test_full_refund_builds_balanced_compensating_journal():
    original = sika_double_entry.validate_batch(
        journal_id="j-original",
        reference="payment:pay-1",
        lines=[
            sika_double_entry.line(account_id="cash", side="debit", amount="100", currency="GBP"),
            sika_double_entry.line(account_id="payable", side="credit", amount="100", currency="GBP"),
        ],
    )
    refund = sika_refund_intent.RefundIntent(
        refund_id="refund-1",
        original_payment_id="pay-1",
        idempotency_key="refund-idem-1",
        amount=Decimal("100.00"),
        currency="GBP",
        status="DRAFT",
        reason="customer_return",
    )
    reversal = sika_refund_intent.compensating_journal(
        refund=refund,
        original_journal=original,
        journal_id="j-refund",
    )
    assert reversal.balanced is True
    assert reversal.posted is False
    assert reversal.reference == "refund:refund-1:payment:pay-1"


def test_refund_status_stays_non_executing():
    status = sika_refund_intent.status()
    assert status["compensating_journal_supported"] is True
    assert status["journal_posting"] is False
    assert status["provider_calling"] is False
    assert status["money_movement"] is False
