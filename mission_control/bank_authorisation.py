"""Real-bank authorisation readiness contract for OAP.

This module does not grant regulatory permission. It records the evidence
categories required to move from a proposed bank concept toward a real UK
bank application and keeps regulated capabilities fail-closed until external
regulatory evidence is explicitly present.
"""
from __future__ import annotations

from typing import Any

PRA_FCA_EVIDENCE = (
    "legal_entity_and_ownership",
    "board_approved_business_plan",
    "bank_business_model_and_products",
    "capital_source_and_proof",
    "liquidity_plan",
    "icaap",
    "ilaap",
    "recovery_and_solvent_exit_plan",
    "governance_and_smr_roles",
    "risk_management_framework",
    "compliance_function",
    "internal_audit_function",
    "aml_ctf_framework",
    "sanctions_screening_and_ofsi_process",
    "consumer_duty_and_complaints",
    "customer_onboarding_kyc",
    "operational_resilience",
    "cyber_and_information_security",
    "outsourcing_and_third_party_risk",
    "financial_crime_monitoring",
    "accounting_audit_and_reconciliation",
    "data_protection_and_recordkeeping",
    "deposit_protection_and_disclosures",
    "treasury_and_asset_liability_management",
    "regulatory_reporting",
    "mobilisation_plan",
    "pra_pre_application_engagement",
    "fca_pre_application_engagement",
    "formal_application_submitted",
    "authorisation_decision_evidence",
)

REGULATED_CAPABILITIES = frozenset(
    {
        "accept_deposits",
        "issue_redeemable_sika",
        "execute_payments",
        "hold_customer_funds",
        "issue_payment_cards",
        "cash_out",
        "foreign_exchange",
        "bank_accounts",
    }
)


def evidence_register() -> dict[str, dict[str, object]]:
    """Return the current bank-authorisation evidence register.

    Evidence starts unproven by design. A later governed evidence store can
    attach regulator references, board approvals, documents and dates.
    """

    return {
        key: {
            "proven": False,
            "evidence_reference": None,
            "reviewed_by": None,
        }
        for key in PRA_FCA_EVIDENCE
    }


def readiness_status(
    *,
    evidence: dict[str, dict[str, object]] | None = None,
) -> dict[str, Any]:
    supplied = evidence or evidence_register()
    proven = [
        key
        for key in PRA_FCA_EVIDENCE
        if bool((supplied.get(key) or {}).get("proven"))
    ]
    missing = [key for key in PRA_FCA_EVIDENCE if key not in proven]
    authorised = "authorisation_decision_evidence" in proven

    return {
        "institution": "United States of Africa Royalty Bank",
        "parent": "ON ANY POSTCODE LTD",
        "jurisdiction": "United Kingdom",
        "route": "PRA/FCA new-bank authorisation",
        "evidence_total": len(PRA_FCA_EVIDENCE),
        "evidence_proven": len(proven),
        "evidence_missing": missing,
        "application_ready": len(missing) == 0,
        "authorised_bank": authorised,
        "deposit_taking_enabled": authorised,
        "regulated_execution_enabled": authorised,
        "humanitarian_or_human_rights_purpose_bypasses_authorisation": False,
        "human_authority_final": True,
    }


def capability_allowed(
    capability: str,
    *,
    regulator_authorisation_proven: bool = False,
    production_gate_passed: bool = False,
) -> bool:
    """Allow regulated capabilities only after real regulator evidence + runtime proof."""

    if capability not in REGULATED_CAPABILITIES:
        return False
    return regulator_authorisation_proven and production_gate_passed
