"""Soul boundary: declared safety policy, never banking or Store authority."""
from __future__ import annotations

from typing import Any

from . import bank_body_integration as body
from . import bank_distribution_intelligence as distribution
from . import prince_sovereign_bank as bank

PROTECTED_CLASSES = (
    "customer_financial_records", "customer_credentials", "bank_signing_keys",
    "founder_private_records", "post_office_cash_records",
)
REQUIRED_RELEASE_PROOFS = (
    "exact_artifact_digest", "independent_signature_verification",
    "publisher_identity", "artifact_bound_guardian_receipt",
    "permissions_and_platform_review", "store_release_receipt",
    "founder_release_approval",
)


def status() -> dict[str, Any]:
    """Read-only composition, with explicit non-operational release status."""
    bank_state = bank.status()
    body_state = body.status()
    store_state = distribution.release_policy()
    return {
        "bank_name": bank_state["name"],
        "heritage_name": bank_state["banking_family"],
        "protected_classes": list(PROTECTED_CLASSES),
        "bank_specific_customer_permission_required": True,
        "postal_permission_is_not_banking_permission": True,
        "founder_institutional_approval_is_not_customer_approval": True,
        "rewards_are_not_customer_money": True,
        "customer_company_community_funds_must_remain_separate": True,
        "third_party_ad_telemetry_allowed": False,
        "public_offline_financial_cache_allowed": False,
        "signing_key_in_store_allowed": False,
        "financial_execution_enabled": False,
        "cash_in_enabled": body_state["post_office"]["cash_in_enabled"],
        "cash_out_enabled": body_state["post_office"]["cash_out_enabled"],
        "install_enabled": store_state["install_enabled"],
        "package_published": store_state["package_published"],
        "release_proofs_required": list(REQUIRED_RELEASE_PROOFS),
        "release_proofs_verified": False,
        "founder_final": True,
    }
