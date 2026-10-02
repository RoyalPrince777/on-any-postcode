from mission_control import sika_double_entry, sika_financial_statements_intelligence


def _accounts():
    return [
        sika_double_entry.account(
            account_id="cash",
            name="Cash",
            account_class="asset",
            currency="GBP",
            jurisdiction="United Kingdom",
        ),
        sika_double_entry.account(
            account_id="liability",
            name="Liability",
            account_class="liability",
            currency="GBP",
            jurisdiction="United Kingdom",
        ),
        sika_double_entry.account(
            account_id="equity",
            name="Equity",
            account_class="equity",
            currency="GBP",
            jurisdiction="United Kingdom",
        ),
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
    ]


def _journals():
    return [
        sika_double_entry.validate_batch(
            journal_id="j-1",
            reference="capital",
            lines=[
                sika_double_entry.line(
                    account_id="cash",
                    side="debit",
                    amount="1000",
                    currency="GBP",
                ),
                sika_double_entry.line(
                    account_id="equity",
                    side="credit",
                    amount="1000",
                    currency="GBP",
                ),
            ],
        ),
        sika_double_entry.validate_batch(
            journal_id="j-2",
            reference="trade",
            lines=[
                sika_double_entry.line(
                    account_id="cash",
                    side="debit",
                    amount="500",
                    currency="GBP",
                ),
                sika_double_entry.line(
                    account_id="revenue",
                    side="credit",
                    amount="500",
                    currency="GBP",
                ),
                sika_double_entry.line(
                    account_id="expense",
                    side="debit",
                    amount="100",
                    currency="GBP",
                ),
                sika_double_entry.line(
                    account_id="cash",
                    side="credit",
                    amount="100",
                    currency="GBP",
                ),
            ],
        ),
    ]


def test_statement_projection_balances():
    result = sika_financial_statements_intelligence.project(
        accounts=_accounts(),
        journals=_journals(),
        cash_account_ids={"cash"},
    )
    assert result.assets == 1400
    assert result.liabilities == 0
    assert result.equity == 1000
    assert result.income == 500
    assert result.expenses == 100
    assert result.profit_or_loss == 400
    assert result.equity_movement == 1400
    assert result.cash_movement == 1400
    assert result.balance_sheet_balanced is True
    assert result.human_review_required is False


def test_status_keeps_statements_non_statutory_and_read_only():
    status = sika_financial_statements_intelligence.status()
    assert status["first_party"] is True
    assert status["statutory_accounts_generated"] is False
    assert status["filing_readiness_claimed"] is False
    assert status["ledger_mutation"] is False
    assert status["money_movement"] is False
