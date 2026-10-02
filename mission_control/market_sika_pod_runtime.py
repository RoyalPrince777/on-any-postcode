"""OAP Market × SIKA × POD governed orchestration spine.

Connects the existing SIKA payment lifecycle, OAP Market order state, Print-on-
Demand supplier readiness and Distribution Runtime into one first-party review
contract. It does not call payment providers or manufacturers. External
execution remains conditional on separately proven provider authority and
receipts.
"""
from __future__ import annotations

from collections.abc import Mapping

from . import (
    distribution_runtime,
    sika_payment_orchestrator,
    sika_payment_submission_evidence,
    sika_secure_provider_runtime,
    supplier_bridge,
)

PAYMENT_ACCEPTED_STATES = frozenset({"AUTHORISED", "SUBMITTED", "SETTLED"})
SUPPLIER_RECEIPT_STATES = frozenset(
    {"ACCEPTED", "IN_PRODUCTION", "SHIPPED", "DELIVERED"}
)


def payment_market_gate(
    *,
    payment_intent: object,
    customer_authority_verified: bool,
    rights_gate_allowed: bool,
    execution_gate_authorised: bool,
) -> dict[str, object]:
    """Evaluate whether one Market payment may advance to provider submission."""

    if not isinstance(payment_intent, Mapping):
        return {
            "ready": False,
            "reason": "payment_intent_invalid",
            "provider_calling": False,
            "money_movement": False,
        }
    status = str(payment_intent.get("status") or "").upper()
    payment_id = str(payment_intent.get("payment_id") or "")
    ready = all(
        (
            bool(payment_id),
            status in {"AUTHORISED", "SUBMITTED", "SETTLED"},
            customer_authority_verified,
            rights_gate_allowed,
            execution_gate_authorised,
        )
    )
    reasons = []
    if not payment_id:
        reasons.append("payment_id_missing")
    if status not in {"AUTHORISED", "SUBMITTED", "SETTLED"}:
        reasons.append("payment_not_authorised")
    if not customer_authority_verified:
        reasons.append("customer_authority_missing")
    if not rights_gate_allowed:
        reasons.append("rights_gate_closed")
    if not execution_gate_authorised:
        reasons.append("execution_gate_closed")
    return {
        "ready": ready,
        "payment_id": payment_id or None,
        "payment_status": status,
        "block_reasons": reasons,
        "provider_submission_eligible": ready and status == "AUTHORISED",
        "provider_calling": False,
        "money_movement": False,
        "human_authority_final": True,
    }


def pod_market_gate(
    *,
    handoff_candidate: object,
    delivery_destination_present: bool,
    payment_capture_proven: bool,
    provider_connector_authorized: bool,
    provider_credentials_configured: bool,
) -> dict[str, object]:
    """Complete the software-side POD handoff decision without executing it."""

    if not isinstance(handoff_candidate, Mapping):
        return {
            "ready": False,
            "reason": "handoff_candidate_invalid",
            "external_submission_performed": False,
        }

    checks = dict(handoff_candidate.get("checks") or {})
    # Replace the four deliberately external blockers with evidence supplied by
    # the governed execution layer. Existing supplier/design facts remain
    # authoritative from the canonical Supplier Bridge candidate.
    checks["delivery_destination_present"] = bool(delivery_destination_present)
    checks["payment_capture_proven"] = bool(payment_capture_proven)
    checks["provider_connector_authorized"] = bool(provider_connector_authorized)
    checks["provider_credentials_configured"] = bool(provider_credentials_configured)
    checks["external_submission_allowed"] = all(
        value
        for key, value in checks.items()
        if key != "external_submission_allowed"
    )
    ready = bool(checks["external_submission_allowed"])
    return {
        "ready": ready,
        "order_id": handoff_candidate.get("order_id"),
        "provider_slug": handoff_candidate.get("provider_slug"),
        "checks": checks,
        "block_reasons": [name for name, passed in checks.items() if not passed],
        "external_submission_allowed": ready,
        "external_submission_performed": False,
        "payment_capture_performed_here": False,
        "money_transfer_performed": False,
        "carrier_dispatch_performed": False,
        "human_authority_final": True,
    }


def payment_submission_receipt_gate(
    *,
    payment_intent: object,
    submission_evidence: object,
) -> dict[str, object]:
    """Require provider submission evidence before claiming payment submission."""

    if not isinstance(payment_intent, Mapping):
        return {"proven": False, "reason": "payment_intent_invalid"}
    if not isinstance(submission_evidence, Mapping):
        return {"proven": False, "reason": "submission_evidence_invalid"}

    payment_id = str(payment_intent.get("payment_id") or "")
    evidence_payment_id = str(submission_evidence.get("payment_id") or "")
    outcome = str(submission_evidence.get("outcome") or "").upper()
    provider_reference = str(submission_evidence.get("provider_reference") or "")
    proven = all(
        (
            payment_id,
            payment_id == evidence_payment_id,
            outcome == "ACCEPTED",
            bool(provider_reference),
        )
    )
    return {
        "proven": proven,
        "payment_id": payment_id or None,
        "provider_reference": provider_reference or None,
        "outcome": outcome,
        "settlement_proven": (
            proven and str(payment_intent.get("status") or "").upper() == "SETTLED"
        ),
        "money_movement_claim_allowed": False,
        "human_authority_final": True,
    }


def supplier_receipt_gate(receipt: object) -> dict[str, object]:
    """Normalize a supplier receipt decision without manufacturing execution."""

    if not isinstance(receipt, Mapping):
        return {"proven": False, "reason": "supplier_receipt_invalid"}
    state = str(receipt.get("state") or "").upper()
    reference = str(receipt.get("provider_reference") or "")
    proven = state in SUPPLIER_RECEIPT_STATES and bool(reference)
    return {
        "proven": proven,
        "state": state,
        "provider_reference": reference or None,
        "production_proven": state in {"IN_PRODUCTION", "SHIPPED", "DELIVERED"},
        "delivery_proven": state == "DELIVERED",
        "external_submission_performed_here": False,
        "human_authority_final": True,
    }


def distribution_transition_for_supplier_state(state: object) -> str | None:
    """Map proven supplier state to the canonical Distribution Runtime."""

    value = str(state or "").upper()
    return {
        "ACCEPTED": "HANDED_OFF",
        "IN_PRODUCTION": "HANDED_OFF",
        "SHIPPED": "HANDED_OFF",
        "DELIVERED": "DELIVERED",
        "FAILED": "RECOVERY_REQUIRED",
        "CANCELLED": "STOPPED",
    }.get(value)


def status() -> dict[str, object]:
    return {
        "system": "OAP Market × SIKA × POD Spine",
        "oap_market_connected": True,
        "sika_payment_orchestrator_connected": bool(
            sika_payment_orchestrator.status().get("persistent_payment_intent")
        ),
        "sika_submission_evidence_connected": bool(
            sika_payment_submission_evidence.status().get("durable_submission_receipts")
        ),
        "pod_supplier_bridge_connected": bool(
            supplier_bridge.truth_status().get("provider_neutral_contract")
        ),
        "distribution_runtime_connected": bool(
            distribution_runtime.status().get("owner_scoped_tracking")
        ),
        "customer_authority_gate_required": True,
        "rights_gate_required": True,
        "execution_gate_required": True,
        "payment_submission_receipt_required": True,
        "supplier_receipt_required": True,
        "refund_contract_required": True,
        "idempotency_required": True,
        "internal_orchestration_ready": True,
        "secure_provider_runtime": sika_secure_provider_runtime.status(),
        "payment_provider_runtime_built": True,
        "pod_provider_runtime_built": True,
        "external_payment_execution_proven": bool(
            sika_secure_provider_runtime.configuration_status("payment").get(
                "configuration_complete"
            )
        ),
        "external_manufacturer_execution_proven": bool(
            sika_secure_provider_runtime.configuration_status("pod").get(
                "configuration_complete"
            )
        ),
        "money_movement_proven": False,
        "human_authority_final": True,
    }
