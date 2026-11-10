from __future__ import annotations

import pytest

from mission_control import sika_account_engine, sika_founder_account


def test_sika_migrations_are_canonical_and_ordered():
    assert sika_account_engine.MIGRATION_VERSION.startswith("0010_")
    assert sika_founder_account.MIGRATION_VERSION.startswith("0011_")
    assert len(sika_account_engine.MIGRATION_CHECKSUM) == 64
    assert len(sika_founder_account.MIGRATION_CHECKSUM) == 64
    assert sika_account_engine.MIGRATION_LOCK_ID != sika_founder_account.MIGRATION_LOCK_ID


def test_founder_schema_refuses_unverified_account_dependency(monkeypatch):
    monkeypatch.setattr(
        sika_account_engine,
        "schema_status",
        lambda: {"schema_ready": False, "error": "sika_account_schema_pending"},
    )
    with pytest.raises(
        sika_founder_account.FounderProvisioningUnavailable,
        match="sika_account_dependency_not_ready",
    ):
        sika_founder_account.init_schema(assume_yes=True)


def test_founder_dry_run_does_not_claim_schema_ready():
    result = sika_founder_account.init_schema(assume_yes=True, dry_run=True)
    assert result["schema_ready"] is False
    assert result["checksum"] == sika_founder_account.MIGRATION_CHECKSUM
    assert result["human_authority_final"] is True
