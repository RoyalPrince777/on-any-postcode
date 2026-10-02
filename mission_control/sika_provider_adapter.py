"""SIKA payment-provider release contract.

This module composes the existing OAP Provider Fabric payment slot with SIKA.
It validates evidence required to enter a later execution review. It does not
call a provider, hold funds, capture payment, execute FX, or settle money.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256

from . import provider_fabric


class ProviderEvidenceError(ValueError):
    """Raised when provider evidence is incomplete or malformed."""


@dataclass(frozen=True)
class ProviderEvidence:
    provider_id: str
    authority_reference: str
    legal_entity_reference: str
    environment: str
    settlement_receipt_contract: str
    refund_contract: str
    evidence_hash: str


def _required_text(value: object, error: str, *, limit: int = 200) -> str:
    text = str(value or "").strip()
    if not text:
        raise ProviderEvidenceError(error)
    return text[:limit]


def build_evidence(
    *,
    provider_id: object,
    authority_reference: object,
    legal_entity_reference: object,
    environment: object,
    settlement_receipt_contract: object,
    refund_contract: object,
) -> ProviderEvidence:
    provider = _required_text(provider_id, "provider_id_required", limit=80)
    authority = _required_text(
        authority_reference, "provider_authority_reference_required"
    )
    entity = _required_text(
        legal_entity_reference, "legal_entity_reference_required"
    )
    env = _required_text(environment, "provider_environment_required", limit=40).lower()
    if env not in {"sandbox", "test", "production"}:
        raise ProviderEvidenceError("provider_environment_invalid")
    receipt = _required_text(
        settlement_receipt_contract, "settlement_receipt_contract_required"
    )
    refund = _required_text(refund_contract, "refund_contract_required")
    digest = sha256(
        "|".join((provider, authority, entity, env, receipt, refund)).encode("utf-8")
    ).hexdigest()
    return ProviderEvidence(
        provider_id=provider,
        authority_reference=authority,
        legal_entity_reference=entity,
        environment=env,
        settlement_receipt_contract=receipt,
        refund_contract=refund,
        evidence_hash=digest,
    )


def release_review(evidence: ProviderEvidence) -> dict[str, object]:
    fabric = provider_fabric.get_private_provider_fabric()
    payment_slots = [
        slot for slot in fabric["slots"] if slot.get("id") == "payments"
    ]
    if len(payment_slots) != 1:
        raise ProviderEvidenceError("canonical_payment_provider_slot_unavailable")

    payment_slot = payment_slots[0]
    provider_fabric_closed = not bool(
        fabric["execution"].get("payment_capture_enabled")
    )
    evidence_complete = all(
        (
            evidence.provider_id,
            evidence.authority_reference,
            evidence.legal_entity_reference,
            evidence.settlement_receipt_contract,
            evidence.refund_contract,
            evidence.evidence_hash,
        )
    )

    may_enter_execution_review = bool(
        evidence_complete
        and provider_fabric_closed
        and fabric["validation"]["passed"]
        and fabric["human_authority_required"]
    )

    return {
        "provider_id": evidence.provider_id,
        "environment": evidence.environment,
        "evidence_hash": evidence.evidence_hash,
        "payment_slot_present": True,
        "provider_fabric_valid": bool(fabric["validation"]["passed"]),
        "provider_fabric_payment_capture_enabled": not provider_fabric_closed,
        "provider_evidence_complete": evidence_complete,
        "settlement_receipt_contract_present": bool(
            evidence.settlement_receipt_contract
        ),
        "refund_contract_present": bool(evidence.refund_contract),
        "human_authority_required": True,
        "may_enter_execution_review": may_enter_execution_review,
        "payment_execution_authorised": False,
        "money_moved": False,
        "customer_funds_held": False,
        "reason": (
            "evidence_complete_for_human_execution_review"
            if may_enter_execution_review
            else "provider_release_gate_closed"
        ),
    }


def status() -> dict[str, object]:
    fabric = provider_fabric.get_private_provider_fabric()
    payment_slot = next(
        (slot for slot in fabric["slots"] if slot.get("id") == "payments"),
        None,
    )
    return {
        "system": "SIKA Provider Adapter",
        "canonical_provider_fabric_reused": True,
        "payment_slot_present": payment_slot is not None,
        "payment_slot_wired": bool(payment_slot and payment_slot.get("wired")),
        "provider_evidence_required": True,
        "settlement_receipt_required": True,
        "refund_contract_required": True,
        "human_authority_required": True,
        "payment_execution_enabled": False,
        "money_movement_enabled": False,
    }
