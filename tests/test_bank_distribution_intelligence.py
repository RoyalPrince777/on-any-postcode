"""Regression: naming, first-party Post Office, and non-installable Store policy."""
from mission_control import bank_distribution_intelligence as dist
from mission_control import prince_sovereign_bank as bank


def test_wider_bank_brand_retains_heritage() -> None:
    state = bank.status()
    assert state["name"] == "United States of Africa Royalty Bank"
    assert state["banking_family"] == "Prince Sovereign Bank"
    assert state["brand_status"] == "proposed; no licence or operational claim"
    assert "post_office" in state["integrations"]
    assert "oap_store" in state["integrations"]


def test_bank_distribution_is_first_party_and_non_installable() -> None:
    status = dist.release_policy()
    assert status["store"] == "OAP Store"
    assert status["publisher"] == "ON ANY POSTCODE LTD"
    assert status["first_party_intelligence"]
    assert status["postal_core_preserved"]
    assert not status["listing_public"]
    assert not status["install_enabled"]
    assert not status["package_published"]
    assert not status["banking_execution_enabled"]
    assert set(status["missing_evidence"]) == dist.REQUIRED_EVIDENCE


def test_claimed_evidence_and_permissions_cannot_publish() -> None:
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
    assert not dist.missing_evidence(claimed)
    result = dist.release_policy(
        claimed, trusted_pipeline_verified=True, territory_authorised=True
    )
    assert not result["install_enabled"]
    assert not result["package_published"]
    assert not result["banking_execution_enabled"]
