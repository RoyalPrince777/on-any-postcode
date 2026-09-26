"""SIKA payment-licence evidence gate.

This gate never grants a licence. It records whether independently verified
regulatory evidence is present before a separately reviewed payment adapter may
be considered for activation.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class PaymentLicenceEvidence:
    jurisdiction: str = "GB"
    regulator: str = "FCA"
    firm_reference_number: str | None = None
    permission_type: str | None = None
    register_status: str | None = None
    payment_services_permission_verified: bool = False
    safeguarding_verified: bool = False
    aml_controls_verified: bool = False
    governance_verified: bool = False
    regulated_adapter_reviewed: bool = False
    production_security_reviewed: bool = False
    human_authority_approved: bool = False
    independent_verification_receipt: str | None = None


REQUIRED = (
    "firm_reference_number",
    "permission_type",
    "register_status",
    "payment_services_permission_verified",
    "safeguarding_verified",
    "aml_controls_verified",
    "governance_verified",
    "regulated_adapter_reviewed",
    "production_security_reviewed",
    "human_authority_approved",
    "independent_verification_receipt",
)


def status(evidence: PaymentLicenceEvidence | None = None) -> dict[str, Any]:
    item = evidence or PaymentLicenceEvidence()
    missing = [name for name in REQUIRED if not getattr(item, name)]
    verified = not missing and item.register_status in {"Authorised", "Registered"}
    return {
        "jurisdiction": item.jurisdiction,
        "regulator": item.regulator,
        "firm_reference_number": item.firm_reference_number,
        "permission_type": item.permission_type,
        "register_status": item.register_status,
        "missing_evidence": missing,
        "licence_evidence_complete": verified,
        "payment_adapter_may_enter_release_review": verified,
        "payment_execution_enabled": False,
        "customer_funds_enabled": False,
        "reason": (
            "licence_evidence_complete_adapter_still_requires_separate_release"
            if verified
            else "verified_regulatory_evidence_required"
        ),
    }
