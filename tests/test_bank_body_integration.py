"""BODY must not convert architecture/Store evidence into financial execution."""
from mission_control import bank_body_integration as body
from mission_control import bank_distribution_intelligence as dist
from mission_control import oap_bank
from mission_control import prince_sovereign_bank as bank


def test_body_reuses_canonical_identity_and_existing_rail() -> None:
    result = body.status()
    assert result["name"] == bank.BANK_NAME
    assert result["banking_family"] == bank.HERITAGE_BANK_NAME
    assert result["technical_rail_id"] == oap_bank.BANK_ID
    assert result["technical_rail_ready_for_planning"]
    assert not result["operational_bank"]
    assert not result["existing_account_or_ledger_created"]


def test_post_office_is_separate_from_post_core_and_cash_access() -> None:
    result = body.status()["post_office"]
    assert result["contract"] == "docs/SIKA_POST_OFFICE_CASH_ACCESS_GAPS.md"
    assert result["post_core_preserved"]
    assert result["bank_specific_permission_required"]
    for name in (
        "cash_in_enabled", "cash_out_enabled", "physical_location_verified",
        "post_office_affiliation_verified",
    ):
        assert result[name] is False


def test_store_is_existing_non_publishing_surface() -> None:
    result = body.status()["store"]
    existing = dist.release_policy()
    assert result["app_id"] == existing["app_id"]
    assert result["install_enabled"] is False
    assert result["package_published"] is False
    assert result["banking_execution_enabled"] is False
    assert result["signing_private_key_available_to_store"] is False


def test_all_financial_and_customer_data_capabilities_disabled() -> None:
    result = body.status()
    for name in (
        "accounts_enabled", "wallet_money_enabled", "ledger_posting_enabled",
        "payment_execution_enabled", "sika_money_issuance_enabled",
        "bank_customer_data_access_enabled",
    ):
        assert result[name] is False
    assert result["human_authority_final"]
