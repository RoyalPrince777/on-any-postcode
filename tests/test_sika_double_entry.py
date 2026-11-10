import pytest

from mission_control import sika_double_entry


def test_balanced_journal_is_accepted_without_posting():
    batch = sika_double_entry.validate_batch(
        journal_id="j-1",
        reference="cash-deposit-proof",
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
    assert batch.balanced is True
    assert batch.posted is False


def test_unbalanced_journal_fails_closed():
    with pytest.raises(sika_double_entry.LedgerError, match="journal_not_balanced"):
        sika_double_entry.validate_batch(
            journal_id="j-2",
            reference="bad-batch",
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
                    amount="99.00",
                    currency="GBP",
                ),
            ],
        )


def test_each_currency_must_balance_independently():
    with pytest.raises(sika_double_entry.LedgerError, match="journal_not_balanced"):
        sika_double_entry.validate_batch(
            journal_id="j-3",
            reference="cross-currency-without-fx-legs",
            lines=[
                sika_double_entry.line(
                    account_id="gbp-cash",
                    side="debit",
                    amount="100.00",
                    currency="GBP",
                ),
                sika_double_entry.line(
                    account_id="ghs-liability",
                    side="credit",
                    amount="100.00",
                    currency="GHS",
                ),
            ],
        )


def test_amounts_must_be_positive_and_finite():
    for bad in ("0", "-1", "NaN", "Infinity"):
        with pytest.raises(
            sika_double_entry.LedgerError,
            match="journal_amount_invalid",
        ):
            sika_double_entry.line(
                account_id="cash",
                side="debit",
                amount=bad,
                currency="GBP",
            )


def test_account_requires_class_currency_and_jurisdiction():
    account = sika_double_entry.account(
        account_id="uk-customer-liability",
        name="UK Customer Liability",
        account_class="liability",
        currency="gbp",
        jurisdiction="United Kingdom",
    )
    assert account.currency == "GBP"
    assert account.account_class is sika_double_entry.AccountClass.LIABILITY


def test_status_keeps_persistence_and_execution_truthful():
    status = sika_double_entry.status()
    assert status["first_party"] is True
    assert status["persistent_journal_store"] is False
    assert status["settlement_execution"] is False
    assert status["external_money_movement"] is False
