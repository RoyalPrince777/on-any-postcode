"""OAP Store Mail listing must not manufacture release or package evidence."""
from __future__ import annotations

from mission_control import mail_store_listing


def test_listing_is_first_party_and_install_locked():
    listing = mail_store_listing.listing()
    assert listing["app_id"] == "oap.mail"
    assert listing["publisher"] == "ON ANY POSTCODE LTD"
    assert listing["distribution"] == "OAP App Store"
    assert listing["first_party"] is True
    assert listing["public_release_state"] == "release_pending"
    assert listing["install_enabled"] is False
    assert listing["package_available"] is False
    assert listing["publish_executed"] is False
    assert listing["mail_delivery_claimed"] is False
    assert listing["end_to_end_encryption_claimed"] is False
    assert listing["security_certification_claimed"] is False
    assert listing["human_authority_final"] is True
    assert not any(listing["gates"].values())


def test_unsupported_or_partial_evidence_does_not_enable_install():
    assert mail_store_listing.listing({"ci_passed": True})["install_enabled"] is False
    assert mail_store_listing.listing({"founder_release_approval": True})[
        "install_enabled"
    ] is False
    assert mail_store_listing.listing({"founder_release_approval": 1})[
        "gates"
    ]["founder_release_approval"] is False


def test_even_declared_complete_evidence_is_not_self_certifying():
    claimed = {key: True for key in mail_store_listing.REQUIRED_RELEASE_EVIDENCE}
    listing = mail_store_listing.listing(claimed)
    assert listing["all_evidence_supplied"] is True
    assert listing["install_enabled"] is False
    assert listing["package_available"] is False
    assert listing["publish_executed"] is False
    assert listing["public_release_state"] == "release_pending"
