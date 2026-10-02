from mission_control import sika_accounting_intelligence, sika_double_entry


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
            account_id="customer-liability",
            name="Customer Liability",
            account_class="liability",
            currency="GBP",
            jurisdiction="United Kingdom",
        ),
        sika_double_entry.account(
            account_id="suspense",
            name="Suspense",
            account_class="liability",
            currency="GBP",
            jurisdiction="United Kingdom",
        ),
    ]


def _balanced_batch(*, credit_account="customer-liability"):
    return sika_double_entry.validate_batch(
        journal_id="j-1",
        reference="deposit",
        lines=[
            sika_double_entry.line(
                account_id="cash",
                side="debit",
                amount="100.00",
                currency="GBP",
            ),
            sika_double_entry.line(
                account_id=credit_account,
                side="credit",
                amount="100.00",
                currency="GBP",
            ),
        ],
    )


def test_accounting_intelligence_reports_structural_readiness():
    result = sika_accounting_intelligence.assess(
        accounts=_accounts(),
        journals=[_balanced_batch()],
        suspense_account_ids={"suspense"},
    )
    assert result.trial_balance_state == "BALANCED"
    assert result.chart_mapping_state == "COMPLETE"
    assert result.suspense_state == "CLEAR"
    assert result.period_control_state == "CLEAR"
    assert result.reversal_state == "CLEAR"
    assert result.statement_readiness == "STRUCTURALLY_READY"
    assert result.human_review_required is False
    assert result.books_modified is False
    assert result.money_moved is False


def test_accounting_intelligence_flags_unmapped_account():
    result = sika_accounting_intelligence.assess(
        accounts=_accounts(),
        journals=[_balanced_batch(credit_account="unknown-liability")],
    )
    assert result.chart_mapping_state == "UNMAPPED_ACCOUNTS"
    assert result.statement_readiness == "REVIEW_REQUIRED"


def test_accounting_intelligence_flags_suspense_exposure():
    result = sika_accounting_intelligence.assess(
        accounts=_accounts(),
        journals=[_balanced_batch(credit_account="suspense")],
        suspense_account_ids={"suspense"},
    )
    assert result.suspense_state == "EXPOSURE"
    assert result.human_review_required is True


def test_accounting_intelligence_flags_period_violation():
    result = sika_accounting_intelligence.assess(
        accounts=_accounts(),
        journals=[_balanced_batch()],
        closed_period_write_attempts=1,
    )
    assert result.period_control_state == "VIOLATION"
    assert result.statement_readiness == "REVIEW_REQUIRED"


def test_accounting_intelligence_flags_unmatched_reversal():
    result = sika_accounting_intelligence.assess(
        accounts=_accounts(),
        journals=[_balanced_batch()],
        unmatched_reversal_count=1,
    )
    assert result.reversal_state == "UNMATCHED"
    assert result.statement_readiness == "REVIEW_REQUIRED"


def test_status_keeps_accounting_intelligence_non_executing():
    status = sika_accounting_intelligence.status()
    assert status["first_party"] is True
    assert status["statutory_accounts_generated"] is False
    assert status["books_mutated"] is False
    assert status["execution_authority"] is False
    assert status["money_movement"] is False
