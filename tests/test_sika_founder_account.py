import re

import pytest

from mission_control import sika_founder_account


def test_founder_schema_enforces_one_owner_account_and_unique_public_number():
    sql = "\n".join(sika_founder_account.SCHEMA_STATEMENTS)
    assert "owner_reference TEXT PRIMARY KEY" in sql
    assert "account_id TEXT NOT NULL UNIQUE" in sql
    assert "sika_number TEXT NOT NULL UNIQUE" in sql
    assert "REFERENCES oap_sika_accounts(account_id)" in sql


def test_founder_number_uses_reserved_namespace_without_personal_data():
    number = sika_founder_account.generate_sika_number()
    assert re.fullmatch(r"SIKA-777-\d{12}", number)


def test_founder_schema_requires_explicit_human_approval():
    with pytest.raises(RuntimeError, match="Explicit human approval required"):
        sika_founder_account.init_schema()


def test_founder_dry_run_does_not_claim_schema_ready():
    result = sika_founder_account.init_schema(assume_yes=True, dry_run=True)
    assert result["schema_ready"] is False
    assert result["human_authority_final"] is True


def test_founder_number_rejects_wrong_namespace_before_database_access(monkeypatch):
    monkeypatch.setattr(
        sika_founder_account.postgres_db,
        "connect",
        lambda *args, **kwargs: pytest.fail("database must not be reached"),
    )
    with pytest.raises(
        sika_founder_account.FounderProvisioningError,
        match="founder_sika_number_namespace_required",
    ):
        sika_founder_account.provision(
            account_id="acct-founder",
            owner_reference="owner-founder",
            legal_entity="ON ANY POSTCODE LTD",
            jurisdiction="United Kingdom",
            currency="GBP",
            ledger_account_id="ledger-founder",
            sika_number="SIKA-123-000000000001",
        )


def test_founder_status_has_no_money_or_treasury_authority():
    status = sika_founder_account.status()
    assert status["one_founder_account_per_owner"] is True
    assert status["public_sika_number"] is True
    assert status["creates_balance"] is False
    assert status["journal_posting"] is False
    assert status["payment_execution"] is False
    assert status["treasury_authority"] is False


def test_founder_provisioning_rejects_non_authority_before_account_insert(monkeypatch):
    calls = []

    class FakeConnection:
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return False
        def execute(self, sql, params=()):
            calls.append(sql)
            pytest.fail("SIKA rows must not be touched for a non-authority owner")

    monkeypatch.setattr(
        sika_founder_account.postgres_db, "connect", lambda *args, **kwargs: FakeConnection()
    )
    monkeypatch.setattr(
        sika_founder_account.authority,
        "require_human_authority",
        lambda connection, identity_id: (_ for _ in ()).throw(
            sika_founder_account.authority.HumanAuthorityRequired(
                "level_zero_human_authority_required"
            )
        ),
    )

    with pytest.raises(
        sika_founder_account.FounderProvisioningError,
        match="human_authority_owner_required",
    ):
        sika_founder_account.provision(
            account_id="acct-founder",
            owner_reference="00000000-0000-4000-8000-000000000777",
            legal_entity="ON ANY POSTCODE LTD",
            jurisdiction="United Kingdom",
            currency="GBP",
            ledger_account_id="ledger-founder",
        )
    assert calls == []
