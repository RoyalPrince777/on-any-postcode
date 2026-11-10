import pytest

from mission_control import sika_account_engine


def test_account_model_only_allows_open_customer_activity():
    open_account = sika_account_engine.BankAccount(
        account_id="acct-1",
        owner_reference="owner-1",
        legal_entity="Europa Crown Bank",
        jurisdiction="United Kingdom",
        currency="GBP",
        ledger_account_id="ledger-1",
        status="OPEN",
    )
    frozen_account = sika_account_engine.BankAccount(
        account_id="acct-1",
        owner_reference="owner-1",
        legal_entity="Europa Crown Bank",
        jurisdiction="United Kingdom",
        currency="GBP",
        ledger_account_id="ledger-1",
        status="FROZEN",
    )
    closed_account = sika_account_engine.BankAccount(
        account_id="acct-1",
        owner_reference="owner-1",
        legal_entity="Europa Crown Bank",
        jurisdiction="United Kingdom",
        currency="GBP",
        ledger_account_id="ledger-1",
        status="CLOSED",
    )
    assert open_account.customer_activity_allowed is True
    assert frozen_account.customer_activity_allowed is False
    assert closed_account.customer_activity_allowed is False


def test_schema_has_identity_and_lifecycle_constraints():
    sql = "\n".join(sika_account_engine.SCHEMA_STATEMENTS)
    assert "owner_reference TEXT NOT NULL" in sql
    assert "legal_entity TEXT NOT NULL" in sql
    assert "jurisdiction TEXT NOT NULL" in sql
    assert "currency TEXT NOT NULL" in sql
    assert "ledger_account_id TEXT NOT NULL UNIQUE" in sql
    assert "status IN ('OPEN','FROZEN','CLOSED')" in sql


def test_schema_init_requires_explicit_human_approval():
    with pytest.raises(RuntimeError, match="Explicit human approval required"):
        sika_account_engine.init_schema()


def test_dry_run_does_not_claim_schema_ready():
    result = sika_account_engine.init_schema(assume_yes=True, dry_run=True)
    assert result["schema_ready"] is False
    assert result["human_authority_final"] is True


def test_status_keeps_account_engine_non_executing():
    status = sika_account_engine.status()
    assert status["first_party"] is True
    assert status["persistent_account_identity"] is True
    assert status["closed_account_reopen_allowed"] is False
    assert status["balance_fabrication"] is False
    assert status["journal_posting"] is False
    assert status["payment_execution"] is False
    assert status["money_movement"] is False


def test_owner_resolver_rejects_mismatch_and_requires_open_account(monkeypatch):
    account = sika_account_engine.BankAccount(
        account_id="acct-owned",
        owner_reference="owner-777",
        legal_entity="Europa Crown Bank",
        jurisdiction="United Kingdom",
        currency="GBP",
        ledger_account_id="ledger-owned",
        status="OPEN",
    )
    monkeypatch.setattr(sika_account_engine, "read_account", lambda account_id: account)

    resolved = sika_account_engine.resolve_owned_account(
        account_id="acct-owned",
        owner_reference="owner-777",
    )
    assert resolved == account

    with pytest.raises(
        sika_account_engine.AccountEngineError,
        match="account_owner_mismatch",
    ):
        sika_account_engine.resolve_owned_account(
            account_id="acct-owned",
            owner_reference="owner-other",
        )


def test_account_status_exposes_owner_resolution():
    assert sika_account_engine.status()["owner_resolution"] is True
