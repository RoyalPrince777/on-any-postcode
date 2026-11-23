"""Private Rabaty merchant launch gate.

This module does not create merchant accounts, publish listings, accept orders,
or infer owner approval. It is a fail-closed eligibility check for later wiring
into the existing OAP Market and OAP Store flows.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RabatyLaunchEvidence:
    owner_authorized: bool = False
    merchant_identity_verified: bool = False
    catalogue_owner_approved: bool = False
    storefront_access_tested: bool = False
    market_publication_approved: bool = False
    ordering_regression_passed: bool = False
    release_gate_passed: bool = False
    apk_device_verified: bool = False


def evaluate_rabaty_launch(evidence: RabatyLaunchEvidence) -> dict[str, object]:
    """Report independent gates; no gate performs publication or execution."""
    if not isinstance(evidence, RabatyLaunchEvidence):
        raise TypeError("rabaty_launch_evidence_required")
    private_preview = evidence.owner_authorized and evidence.merchant_identity_verified
    public_listing = (
        private_preview
        and evidence.catalogue_owner_approved
        and evidence.storefront_access_tested
        and evidence.market_publication_approved
        and evidence.release_gate_passed
    )
    ordering = public_listing and evidence.ordering_regression_passed
    native_install = public_listing and evidence.apk_device_verified
    return {
        "merchant": "Rabaty Food Centre",
        "private_preview_eligible": private_preview,
        "public_listing_eligible": public_listing,
        "ordering_eligible": ordering,
        "native_install_eligible": native_install,
        "execution_performed": False,
        "human_authority_final": True,
    }
