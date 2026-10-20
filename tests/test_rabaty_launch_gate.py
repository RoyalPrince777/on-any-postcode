"""Negative tests for Rabaty private launch eligibility."""
import pytest

from mission_control.rabaty_launch_gate import (
    RabatyLaunchEvidence,
    evaluate_rabaty_launch,
)


def test_default_is_private_and_non_orderable():
    result = evaluate_rabaty_launch(RabatyLaunchEvidence())
    assert not any(result[key] for key in (
        "private_preview_eligible", "public_listing_eligible",
        "ordering_eligible", "native_install_eligible",
    ))
    assert result["execution_performed"] is False


def test_owner_approval_alone_is_insufficient():
    result = evaluate_rabaty_launch(RabatyLaunchEvidence(owner_authorized=True))
    assert result["private_preview_eligible"] is False


def test_private_preview_never_implies_publication():
    result = evaluate_rabaty_launch(RabatyLaunchEvidence(
        owner_authorized=True, merchant_identity_verified=True,
    ))
    assert result["private_preview_eligible"] is True
    assert result["public_listing_eligible"] is False


def test_ordering_and_apk_require_independent_proof():
    result = evaluate_rabaty_launch(RabatyLaunchEvidence(
        owner_authorized=True, merchant_identity_verified=True,
        catalogue_owner_approved=True, storefront_access_tested=True,
        market_publication_approved=True, release_gate_passed=True,
    ))
    assert result["public_listing_eligible"] is True
    assert result["ordering_eligible"] is False
    assert result["native_install_eligible"] is False


def test_missing_release_gate_blocks_publication():
    result = evaluate_rabaty_launch(RabatyLaunchEvidence(
        owner_authorized=True, merchant_identity_verified=True,
        catalogue_owner_approved=True, storefront_access_tested=True,
        market_publication_approved=True, ordering_regression_passed=True,
        apk_device_verified=True,
    ))
    assert result["public_listing_eligible"] is False
    assert result["ordering_eligible"] is False


def test_rejects_unknown_evidence():
    with pytest.raises(TypeError):
        evaluate_rabaty_launch({})
