"""Founder-only OAP Bank orchestration contract.

This module defines OAP's future financial front-door architecture without enabling
payment, custody, transfer initiation or regulated banking activity. External bank
connections remain locked until an approved regulated integration and compliance
proof exist. Human Authority remains final.
"""

from __future__ import annotations

from typing import Any

BANK_ID = "oap-bank"
BANK_NAME = "OAP Bank"


def status() -> dict[str, Any]:
    """Return the secret-free, non-payment OAP Bank architecture contract."""

    return {
        "id": BANK_ID,
        "name": BANK_NAME,
        "ready": True,
        "surface": "Founder-only financial orchestration planning",
        "mode": "routing and account-connection readiness only",
        "purpose": (
            "Provide one OAP-controlled financial front door that can later connect "
            "supported regulated banks or authorised Open Banking providers without "
            "making OAP the custodian or payment initiator by default."
        ),
        "bank_policy": {
            "supported_bank_goal": "any bank supported by an approved regulated connector",
            "external_bank_is_custodian": True,
            "oap_holds_customer_funds": False,
            "oap_initiates_payments": False,
            "oap_executes_transfers": False,
            "oap_issues_bank_accounts": False,
            "oap_claims_regulated_bank_status": False,
            "payment_enabled": False,
            "open_banking_live": False,
        },
        "future_flow": [
            "OAP interface",
            "user consent",
            "approved regulated bank/Open Banking connector",
            "customer bank",
            "provider receipt",
            "HRM audit receipt",
        ],
        "governance": {
            "human_authority_final": True,
            "compliance_before_activation": True,
            "provider_receipt_required": True,
            "secrets_exposed": False,
            "public_bank_claim_locked_until_approval": True,
        },
    }
