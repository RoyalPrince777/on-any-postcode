from datetime import date

import pytest

from mission_control import (
    sika_accounting_controls,
    sika_closing_retained_earnings,
    sika_double_entry,
)


def _period(status="CLOSED"):
    return sika_accounting_controls.PeriodState(
        period_id="2026-10-UK",
        jurisdiction="United Kingdom",
        start_date=date(2026, 10, 1),
        end_date=date(2026, 10, 31),
        status=status,
    )


def _accounts():
    return [
        sika_double_entry.account(
            account_id="revenue",
            name="Revenue",
            account_class="income",
            currency="GBP",
            jurisdiction="United Kingdom",
        ),
        sika_double_entry.account(
            account_id="expense",
            name="Expense",
            account_class="expense",
            currency="GBP",
            jurisdiction="United Kingdom",
        ),
        sika_double_entry.account(
            account_id="retained-earnings",
            name="Retained Earnings",
            account_class="equity",
            currency="GBP",
            jurisdiction="United Kingdom",
        ),
    ]


def _journal():
    return sika_double_entry.validate_batch(
        journal_id="j-1",
        reference="period-activity",
        lines=[
            sika_double_entry.line(
                account_id="cash",
                side="debit",
                amount="1000",
                currency="GBP",
            ),
            sika_double_entry.line(
                account_id="revenue",
                side="credit",
                amount="1000",
                currency="GBP",
            ),
            sika_double_entry.line(
                account_id="expense",
                side="debit",
                amount="250",
                currency="GBP",
            ),
            sika_double_entry.line(
                account_id="cash",
                side="credit",
                amount="250",
                currency="GBP",
            ),
        ],
    )


def test_profitable_period_closes_into_retained_earnings():
    result = sika_closing_retained_earnings.build_close(
        period=_period(),
        accounts=_accounts(),
        journals=[_journal()],
        retained_earnings_account_id="retained-earnings",
        closing_journal_id="close-1",
        reference="close-2026-10",
    )
    assert result.profit_or_loss == 750
    assert result.closing_batch.balanced is True
    assert result.source_journals_modified is False
    assert result.money_moved is False
    assert result.closing_batch.lines[-1].account_id == "retained-earnings"
    assert result.closing_batch.lines[-1].side is sika_double_entry.Side.CREDIT


def test_open_period_cannot_close():
    with pytest.raises(
        sika_closing_retained_earnings.ClosingError,
        match="accounting_period_must_be_closed",
    ):
        sika_closing_retained_earnings.build_close(
            period=_period(status="OPEN"),
            accounts=_accounts(),
            journals=[_journal()],
            retained_earnings_account_id="retained-earnings",
            closing_journal_id="close-1",
            reference="close-2026-10",
        )


def test_retained_earnings_must_be_equity():
    accounts = _accounts()
    accounts[-1] = sika_double_entry.account(
        account_id="retained-earnings",
        name="Wrong",
        account_class="liability",
        currency="GBP",
        jurisdiction="United Kingdom",
    )
    with pytest.raises(
        sika_closing_retained_earnings.ClosingError,
        match="retained_earnings_account_must_be_equity",
    ):
        sika_closing_retained_earnings.build_close(
            period=_period(),
            accounts=accounts,
            journals=[_journal()],
            retained_earnings_account_id="retained-earnings",
            closing_journal_id="close-1",
            reference="close-2026-10",
        )


def test_status_keeps_closing_non_executing():
    status = sika_closing_retained_earnings.status()
    assert status["first_party"] is True
    assert status["source_journal_mutation"] is False
    assert status["statutory_accounts_generated"] is False
    assert status["settlement_execution"] is False
    assert status["money_movement"] is False
