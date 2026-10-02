import pytest

from mission_control import sika_double_entry, sika_runtime_reconciliation


def _journal():
    return sika_double_entry.validate_batch(
        journal_id="j-1",
        reference="provider-order-777",
        lines=[
            sika_double_entry.line(
                account_id="settlement-cash",
                side="debit",
                amount="100.00",
                currency="GBP",
            ),
            sika_double_entry.line(
                account_id="customer-liability",
                side="credit",
                amount="100.00",
                currency="GBP",
            ),
        ],
    )


def _receipt(**overrides):
    values = {
        "provider_id": "provider-a",
        "provider_reference": "settlement-1",
        "journal_reference": "provider-order-777",
        "amount": "100.00",
        "currency": "GBP",
        "settlement_status": "SETTLED",
        "evidence_hash": "abc123",
    }
    values.update(overrides)
    return sika_runtime_reconciliation.receipt(**values)


def test_matching_settlement_reconciles_without_mutation():
    result = sika_runtime_reconciliation.reconcile(
        journal=_journal(),
        settlement=_receipt(),
    )
    assert result.state == "MATCHED"
    assert result.reference_match is True
    assert result.amount_match is True
    assert result.currency_match is True
    assert result.settlement_final is True
    assert result.human_review_required is False
    assert result.journal_modified is False
    assert result.money_moved is False


def test_amount_mismatch_requires_review():
    result = sika_runtime_reconciliation.reconcile(
        journal=_journal(),
        settlement=_receipt(amount="99.00"),
    )
    assert result.state == "MISMATCH"
    assert result.amount_match is False
    assert result.human_review_required is True


def test_pending_settlement_never_reports_match():
    result = sika_runtime_reconciliation.reconcile(
        journal=_journal(),
        settlement=_receipt(settlement_status="PENDING"),
    )
    assert result.state == "PENDING"
    assert result.settlement_final is False
    assert result.human_review_required is True


def test_failed_settlement_is_exception():
    result = sika_runtime_reconciliation.reconcile(
        journal=_journal(),
        settlement=_receipt(settlement_status="FAILED"),
    )
    assert result.state == "EXCEPTION"
    assert result.human_review_required is True


def test_invalid_receipt_fails_closed():
    with pytest.raises(
        sika_runtime_reconciliation.ReconciliationError,
        match="settlement_status_invalid",
    ):
        _receipt(settlement_status="UNKNOWN")


def test_status_keeps_reconciliation_non_executing():
    status = sika_runtime_reconciliation.status()
    assert status["first_party"] is True
    assert status["automatic_retry"] is False
    assert status["journal_mutation"] is False
    assert status["settlement_execution"] is False
    assert status["money_movement"] is False
