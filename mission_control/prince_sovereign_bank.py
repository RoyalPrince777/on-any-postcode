"""First-party Prince Sovereign Bank master contract (no financial execution).

Mind, Body and Soul are intentionally separate from mission_control.oap_bank:
the older connector-readiness rail is preserved, while this contract states
the owner-operated bank vision without misrepresenting operational readiness.
"""
from __future__ import annotations

from typing import Any

BANK_NAME = "Prince Sovereign Bank"
CURRENCY_NAME = "SIKA"
SUBUNIT_NAME = "SEEDS"
SUBUNITS_PER_SIKA = 100

MIND = (
    "first_party_financial_intelligence",
    "certified_identity_and_bank_specific_permissions",
    "separate_rewards_fiat_and_proposed_currency",
    "risk_and_fraud_review",
    "founder_institutional_authority",
    "customer_transaction_authority",
    "twenty_one_signal_governance",
)
BODY = (
    "wallet", "double_entry_ledger", "payment_rail", "cards",
    "exchange", "market", "runner", "treasury", "notes", "coins",
    "accounts", "reconciliation", "recovery",
)
SOUL = (
    "no_third_party_telemetry", "no_external_ai_authority",
    "segregated_customer_company_community_funds",
    "private_financial_records", "auditable_decisions",
    "lawful_financial_authorisation", "human_approved_execution",
)
INTEGRATIONS = (
    "oap_world", "market", "post_core", "movement", "global_transport",
    "media", "distribution", "community_treasury",
)
REGULATED_CAPABILITIES = frozenset({
    "deposits", "payment_execution", "cash_out", "issued_cards",
    "foreign_exchange", "bank_accounts", "notes", "coins",
})


def status() -> dict[str, Any]:
    """Return an honest architecture snapshot, not an operational bank claim."""
    return {
        "name": BANK_NAME,
        "institutional_vision": "United States of Africa Royalty Bank",
        "parent": "ON ANY POSTCODE LTD",
        "currency": {
            "name": CURRENCY_NAME,
            "subunit": SUBUNIT_NAME,
            "subunits_per_unit": SUBUNITS_PER_SIKA,
            "rewards_are_money": False,
            "proposed_currency_is_legal_tender": False,
        },
        "mind": list(MIND),
        "body": list(BODY),
        "soul": list(SOUL),
        "integrations": list(INTEGRATIONS),
        "first_party_core": True,
        "operational_bank": False,
        "regulated_execution_enabled": False,
        "licence_verified": False,
        "production_tested": False,
        "founder_final_for_institutional_changes": True,
        "customer_approval_required_for_transactions": True,
        "existing_oap_bank_rail_preserved": True,
    }


def capability_allowed(
    capability: str,
    *,
    authorised: bool = False,
    customer_approved: bool = False,
    production_gate_passed: bool = False,
) -> bool:
    """Fail closed: planning never becomes money movement by toggling a flag.

    The architecture contract is deliberately non-executing even when callers
    supply booleans; actual regulated services require separately reviewed code.
    """
    del authorised, customer_approved, production_gate_passed
    if capability in REGULATED_CAPABILITIES:
        return False
    return False
