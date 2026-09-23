"""First-party OAP Store distribution gate for the proposed USA Royalty Bank.

Pure, side-effect-free policy. A caller cannot make a package installable merely
by claiming approval. Only a separately authenticated artifact pipeline may
provide evidence; this module does not publish packages or enable banking.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

APP_ID = "oap.usa_royalty_bank"
DISPLAY_NAME = "United States of Africa Royalty Bank"
HERITAGE_BANK = "Prince Sovereign Bank"
STORE = "OAP Store"
CHANNELS = ("android", "pwa")
REQUIRED_EVIDENCE = frozenset({
    "artifact_sha256", "publisher_signature", "publisher_identity",
    "guardian_scan", "permission_review", "platform_compatibility",
    "security_review", "founder_release_approval",
})


@dataclass(frozen=True)
class PackageEvidence:
    """Immutable artifact metadata; strings are not proof by themselves."""

    artifact_sha256: str | None = None
    publisher_signature: str | None = None
    publisher_identity: str | None = None
    guardian_scan: bool = False
    permission_review: bool = False
    platform_compatibility: bool = False
    security_review: bool = False
    founder_release_approval: bool = False


def missing_evidence(package: PackageEvidence | None = None) -> tuple[str, ...]:
    """List missing inputs, without asserting that supplied inputs are verified."""
    if package is None:
        return tuple(sorted(REQUIRED_EVIDENCE))
    present = {
        key for key in REQUIRED_EVIDENCE
        if getattr(package, key, None)
    }
    return tuple(sorted(REQUIRED_EVIDENCE - present))


def release_policy(
    package: PackageEvidence | None = None,
    *,
    trusted_pipeline_verified: bool = False,
    territory_authorised: bool = False,
) -> dict[str, Any]:
    """Fail closed until a separate verified package distribution implementation.

    A release manifest, even complete, is not a signed package. This API cannot
    publish or install anything and territory permission never grants banking
    execution, deposits, transfers or currency issuance.
    """
    del trusted_pipeline_verified, territory_authorised
    return {
        "app_id": APP_ID,
        "name": DISPLAY_NAME,
        "banking_family": HERITAGE_BANK,
        "store": STORE,
        "channels": list(CHANNELS),
        "publisher": "ON ANY POSTCODE LTD",
        "first_party_intelligence": True,
        "post_office_integration": "separate; bank-specific permission required",
        "postal_core_preserved": True,
        "listing_public": False,
        "install_enabled": False,
        "package_published": False,
        "banking_execution_enabled": False,
        "missing_evidence": list(missing_evidence(package)),
        "reason": "No signed, independently verified installable release is registered.",
    }
