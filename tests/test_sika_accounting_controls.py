from datetime import date

import pytest

from mission_control import sika_accounting_controls, sika_double_entry


def test_period_state_blocks_posting_when_closed():
    state = sika_accounting_controls.PeriodState(
        period_id="2026-10-UK",
        jurisdiction="United Kingdom",
        start_date=date(2026, 10, 1),
        end_date=date(2026, 10, 31),
        status="CLOSED",
    )
    assert state.posting_allowed is False


def test_period_state_allows_posting_when_open():
    state = sika_accounting_controls.PeriodState(
        period_id="2026-10-GH",
        jurisdiction="Ghana",
        start_date=date(2026, 10, 1),
        end_date=date(2026, 10, 31),
        status="OPEN",
    )
    assert state.posting_allowed is True


def test_schema_has_chart_and_period_constraints():
    sql = "\n".join(sika_accounting_controls.SCHEMA_STATEMENTS)
    assert "oap_sika_chart_accounts" in sql
    assert "oap_sika_accounting_periods" in sql
    assert "status IN ('OPEN','CLOSED')" in sql
    assert "account_class IN ('asset','liability','equity','income','expense')" in sql


def test_schema_init_requires_human_authority():
    with pytest.raises(RuntimeError, match="Explicit human approval required"):
        sika_accounting_controls.init_schema()


def test_period_validation_rejects_bad_range():
    with pytest.raises(ValueError, match="period_date_range_invalid"):
        sika_accounting_controls.create_period(
            period_id="bad",
            jurisdiction="Ghana",
            start_date=date(2026, 10, 31),
            end_date=date(2026, 10, 1),
        )


def test_chart_account_model_remains_typed():
    account = sika_double_entry.account(
        account_id="cash-gbp",
        name="Cash GBP",
        account_class="asset",
        currency="GBP",
        jurisdiction="United Kingdom",
    )
    assert account.account_class is sika_double_entry.AccountClass.ASSET


def test_status_keeps_controls_non_executing():
    status = sika_accounting_controls.status()
    assert status["chart_of_accounts_persistent"] is True
    assert status["accounting_periods_persistent"] is True
    assert status["closed_period_posting_block"] is True
    assert status["settlement_execution"] is False
    assert status["money_movement"] is False
