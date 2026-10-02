"""Single governed SIKA Pay Gateway for OAP World.

This module provides one first-party authorization door for payment-capable OAP
surfaces. It binds a canonical SIKA Rights Decision Record to payment
authorization readiness. It does not call providers, settle funds, post
journals, or move money.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any

from . import sika_rights_decision_record

SURFACES = frozenset({
    "OAP World",
    "OAP Market",
    "OAP Music",
    "OAP Events",
    "OAP Records",
    "OAP Arena",
    "My World",
    "Founder Business Creator",
})


class SikaPayGatewayError(ValueError):
    """Raised when the unified SIKA Pay contract is invalid."""


def _required(value: object, field: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise SikaPayGatewayError(f"{field}_required")
    return text


def _amount(value: object) -> str:
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise SikaPayGatewayError("amount_invalid") from exc
    if not parsed.is_finite() or parsed <= 0:
        raise SikaPayGatewayError("amount_invalid")
    return f"{parsed.quantize(Decimal('0.01')):.2f}"


@dataclass(frozen=True)
class PayRequest:
    surface: str
    payment_id: str
    payer_account_id: str
    payee_reference: str
    amount: str
    currency: str
    jurisdiction: str
    rights_record_hash: str
    rights_gate_decision_hash: str

    def as_dict(self) -> dict[str, str]:
        return {
            "surface": self.surface,
            "payment_id": self.payment_id,
            "payer_account_id": self.payer_account_id,
            "payee_reference": self.payee_reference,
            "amount": self.amount,
            "currency": self.currency,
            "jurisdiction": self.jurisdiction,
            "rights_record_hash": self.rights_record_hash,
            "rights_gate_decision_hash": self.rights_gate_decision_hash,
        }


def build_pay_request(
    *,
    surface: object,
    payment_id: object,
    payer_account_id: object,
    payee_reference: object,
    amount: object,
    currency: object,
    jurisdiction: object,
    rights_record: object,
) -> dict[str, Any]:
    """Return one bounded SIKA Pay authorization object.

    The gateway reports ready_for_payment_authorisation only when:
    - the surface is an approved OAP payment surface,
    - the SIKA Rights Decision Record verifies,
    - the underlying rights decision is ALLOW,
    - the rights execution gate reports readiness.

    Readiness is not settlement, provider submission, or money movement.
    """
    surface_value = _required(surface, "surface")
    if surface_value not in SURFACES:
        raise SikaPayGatewayError("surface_not_registered")

    if not isinstance(rights_record, Mapping):
        raise SikaPayGatewayError("rights_record_required")

    check = sika_rights_decision_record.verify_decision_record(rights_record)
    if not check.get("verified"):
        raise SikaPayGatewayError("rights_record_integrity_failed")

    gate = sika_rights_decision_record.execution_gate(rights_record)
    if not gate.get("ready"):
        return {
            "ready_for_payment_authorisation": False,
            "reason": gate.get("reason") or "rights_gate_not_ready",
            "provider_calling": False,
            "settlement_execution": False,
            "money_movement": False,
            "human_authority_final": True,
        }

    request = PayRequest(
        surface=surface_value,
        payment_id=_required(payment_id, "payment_id"),
        payer_account_id=_required(payer_account_id, "payer_account_id"),
        payee_reference=_required(payee_reference, "payee_reference"),
        amount=_amount(amount),
        currency=_required(currency, "currency").upper(),
        jurisdiction=_required(jurisdiction, "jurisdiction"),
        rights_record_hash=str(rights_record["record_hash"]),
        rights_gate_decision_hash=str(rights_record["gate_decision_hash"]),
    )
    return {
        **request.as_dict(),
        "ready_for_payment_authorisation": True,
        "requires_payment_orchestrator": True,
        "requires_external_authorized_executor": True,
        "provider_calling": False,
        "journal_posting": False,
        "settlement_execution": False,
        "money_movement": False,
        "human_authority_final": True,
    }


def authorize_orchestrator_transition(
    *,
    pay_request: object,
    current_status: object,
) -> dict[str, Any]:
    """Authorize only the REVIEW -> AUTHORISED transition contractually.

    This function does not mutate the payment orchestrator. It produces a
    bounded authorization decision that callers can enforce before invoking a
    state transition.
    """
    if not isinstance(pay_request, Mapping):
        raise SikaPayGatewayError("pay_request_invalid")
    if pay_request.get("ready_for_payment_authorisation") is not True:
        return {
            "transition_authorized": False,
            "reason": "pay_request_not_ready",
            "target_status": None,
        }
    if str(current_status or "").upper() != "REVIEW":
        return {
            "transition_authorized": False,
            "reason": "payment_not_in_review",
            "target_status": None,
        }
    return {
        "transition_authorized": True,
        "reason": None,
        "target_status": "AUTHORISED",
        "surface": str(pay_request.get("surface") or ""),
        "payment_id": str(pay_request.get("payment_id") or ""),
        "payer_account_id": str(pay_request.get("payer_account_id") or ""),
        "payee_reference": str(pay_request.get("payee_reference") or ""),
        "amount": str(pay_request.get("amount") or ""),
        "currency": str(pay_request.get("currency") or ""),
        "jurisdiction": str(pay_request.get("jurisdiction") or ""),
        "rights_record_hash": str(pay_request.get("rights_record_hash") or ""),
        "rights_gate_decision_hash": str(
            pay_request.get("rights_gate_decision_hash") or ""
        ),
        "provider_calling": False,
        "settlement_execution": False,
        "money_movement": False,
        "human_authority_final": True,
    }


def status() -> dict[str, Any]:
    return {
        "system": "SIKA Pay Gateway",
        "first_party": True,
        "registered_surfaces": tuple(sorted(SURFACES)),
        "rights_record_required": True,
        "rights_allow_required": True,
        "single_payment_door": True,
        "payment_orchestrator_required": True,
        "external_authorized_executor_required": True,
        "provider_calling": False,
        "settlement_execution": False,
        "money_movement": False,
        "human_authority_final": True,
    }
