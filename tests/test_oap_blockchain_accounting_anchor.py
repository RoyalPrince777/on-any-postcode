import pytest

from mission_control import (
    oap_blockchain_accounting_anchor,
    sika_double_entry,
    sika_runtime_reconciliation,
)


def _journal():
    return sika_double_entry.validate_batch(
        journal_id="j-777",
        reference="settlement-777",
        lines=[
            sika_double_entry.line(
                account_id="cash",
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


def test_journal_hash_is_deterministic():
    journal = _journal()
    first = oap_blockchain_accounting_anchor.journal_evidence_hash(journal)
    second = oap_blockchain_accounting_anchor.journal_evidence_hash(journal)
    assert first == second
    assert len(first) == 64


def test_reconciliation_hash_is_deterministic():
    result = sika_runtime_reconciliation.ReconciliationResult(
        state="MATCHED",
        reference_match=True,
        amount_match=True,
        currency_match=True,
        settlement_final=True,
        human_review_required=False,
    )
    digest = oap_blockchain_accounting_anchor.reconciliation_evidence_hash(result)
    assert len(digest) == 64


def test_anchor_is_chainable_and_verifiable():
    evidence = oap_blockchain_accounting_anchor.journal_evidence_hash(_journal())
    anchor = oap_blockchain_accounting_anchor.anchor(
        anchor_id="a-1",
        jurisdiction="United Kingdom",
        domain="journal",
        subject_reference="j-777",
        previous_hash="0" * 64,
        evidence_hash=evidence,
    )
    assert len(anchor.current_hash) == 64
    assert oap_blockchain_accounting_anchor.verify(anchor) is True


def test_anchor_fails_closed_for_invalid_hash():
    with pytest.raises(
        oap_blockchain_accounting_anchor.AnchorError,
        match="anchor_previous_hash_invalid",
    ):
        oap_blockchain_accounting_anchor.anchor(
            anchor_id="a-1",
            jurisdiction="Ghana",
            domain="journal",
            subject_reference="j-1",
            previous_hash="bad",
            evidence_hash="0" * 64,
        )


def test_anchor_rejects_unknown_domain():
    with pytest.raises(
        oap_blockchain_accounting_anchor.AnchorError,
        match="anchor_domain_invalid",
    ):
        oap_blockchain_accounting_anchor.anchor(
            anchor_id="a-1",
            jurisdiction="Ghana",
            domain="crypto",
            subject_reference="j-1",
            previous_hash="0" * 64,
            evidence_hash="0" * 64,
        )


def test_status_makes_non_crypto_boundary_explicit():
    status = oap_blockchain_accounting_anchor.status()
    assert status["first_party"] is True
    assert status["cryptocurrency"] is False
    assert status["token_issued"] is False
    assert status["mining"] is False
    assert status["settlement_execution"] is False
    assert status["money_movement"] is False
