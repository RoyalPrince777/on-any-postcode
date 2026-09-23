"""Public USA Royalty Bank information only; no installable artifact or banking."""
from __future__ import annotations

from . import bank_distribution_intelligence as distribution
from . import prince_sovereign_bank as bank


def listing() -> dict[str, object]:
    """Public-safe read-only listing from the existing bank/Store policy."""
    state = distribution.release_policy()
    return {
        "app_id": state["app_id"],
        "name": bank.BANK_NAME,
        "heritage": bank.HERITAGE_BANK_NAME,
        "publisher": state["publisher"],
        "store": state["store"],
        "description": "Proposed OAP first-party banking application. No banking services or installable release.",
        "first_party": True,
        "informational_only": True,
        "public_release_state": "release_pending",
        "install_enabled": False,
        "package_available": False,
        "package_published": False,
        "banking_execution_enabled": False,
        "cash_services_enabled": False,
        "currency_issuance_enabled": False,
        "signed_package_verified": False,
        "separate_bank_pwa_verified": False,
        "human_authority_final": True,
    }
