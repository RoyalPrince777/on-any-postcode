"""Read-only BODY integration of the existing OAP Bank, SIKA and Store contracts.

This is a composition of existing non-operational modules, not a new account,
payment, signing, cash or distribution engine. No I/O, persistence or actions.
"""
from __future__ import annotations

from typing import Any

from . import bank_distribution_intelligence as distribution
from . import oap_bank
from . import prince_sovereign_bank as bank

POST_OFFICE_CONTRACT = "docs/SIKA_POST_OFFICE_CASH_ACCESS_GAPS.md"
SIKA_APP_CONTRACT = "docs/SIKA_INSTALLABLE_MONEY_APP_CONTRACT.md"
STORE_CONTRACT = "mission_control/ecosystem_handoff.py"


def status() -> dict[str, Any]:
    """Compose declarations without upgrading a planning-ready rail to a bank."""
    identity = bank.status()
    legacy = oap_bank.status()
    store = distribution.release_policy()
    return {
        "name": identity["name"],
        "banking_family": identity["banking_family"],
        "technical_rail_id": legacy["id"],
        "technical_rail_mode": legacy["mode"],
        "technical_rail_ready_for_planning": legacy["ready"],
        "operational_bank": False,
        "accounts_enabled": False,
        "wallet_money_enabled": False,
        "ledger_posting_enabled": False,
        "payment_execution_enabled": False,
        "sika_money_issuance_enabled": False,
        "bank_customer_data_access_enabled": False,
        "post_office": {
            "contract": POST_OFFICE_CONTRACT,
            "post_core_preserved": True,
            "cash_in_enabled": False,
            "cash_out_enabled": False,
            "physical_location_verified": False,
            "post_office_affiliation_verified": False,
            "bank_specific_permission_required": True,
        },
        "store": {
            "contract": STORE_CONTRACT,
            "app_id": store["app_id"],
            "install_enabled": store["install_enabled"],
            "package_published": store["package_published"],
            "banking_execution_enabled": store["banking_execution_enabled"],
            "signing_private_key_available_to_store": False,
        },
        "sika_contract": SIKA_APP_CONTRACT,
        "existing_account_or_ledger_created": False,
        "human_authority_final": True,
    }
