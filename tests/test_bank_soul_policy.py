"""Soul regression: claimed approvals cannot become release or banking proof."""
from mission_control import bank_distribution_intelligence as dist
from mission_control import bank_soul_policy as soul


def test_all_claimed_evidence_remains_unverified() -> None:
    claimed = dist.PackageEvidence(
        artifact_sha256="a" * 64,
        publisher_signature="unverified-signature",
        publisher_identity="ON ANY POSTCODE LTD",
        guardian_scan=True,
        permission_review=True,
        platform_compatibility=True,
        security_review=True,
        founder_release_approval=True,
    )
    result = dist.release_policy(
        claimed, trusted_pipeline_verified=True, territory_authorised=True
    )
    assert result["missing_evidence"] == []
    assert set(result["unverified_evidence"]) == dist.REQUIRED_EVIDENCE
    assert result["verified_evidence"] == []
    assert result["artifact_bound_receipt"] is None
    assert result["signing_key_access"] is False
    assert result["founder_approval_is_not_package_proof"]
    assert not result["install_enabled"]
    assert not result["package_published"]


def test_soul_keeps_post_office_customer_and_store_boundaries() -> None:
    result = soul.status()
    assert result["postal_permission_is_not_banking_permission"]
    assert result["founder_institutional_approval_is_not_customer_approval"]
    assert result["bank_specific_customer_permission_required"]
    assert result["rewards_are_not_customer_money"]
    assert result["customer_company_community_funds_must_remain_separate"]
    assert not result["third_party_ad_telemetry_allowed"]
    assert not result["public_offline_financial_cache_allowed"]
    assert not result["signing_key_in_store_allowed"]
    assert not result["cash_in_enabled"]
    assert not result["cash_out_enabled"]
    assert not result["financial_execution_enabled"]
    assert not result["install_enabled"]
    assert not result["package_published"]
    assert not result["release_proofs_verified"]
