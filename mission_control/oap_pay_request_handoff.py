"""Bounded handoff from an OAP Pay request into the SIKA payment pipeline.

This module binds one OPEN, non-expired payment request to a payer account and
creates the canonical draft PaymentIntent plus customer-authority receipt.
It does not authorize REVIEW -> AUTHORISED, call providers, settle, or move money.
"""
from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timezone
from typing import Any

from . import (
    sika_account_engine,
    sika_customer_payment_authority,
    sika_payment_orchestrator,
)


class PaymentRequestHandoffError(ValueError):
    """Raised when a payment request cannot safely enter the payment pipeline."""


def _required(value: object, field: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise PaymentRequestHandoffError(f"{field}_required")
    return text


def _request_field(request: Mapping[str, Any], field: str) -> str:
    return _required(request.get(field), field)


def build_handoff(
    *,
    request: object,
    payer_account: object,
    payment_id: object,
    idempotency_key: object,
    authority_reference: object,
    authorised_at: object,
    expires_at: object,
) -> dict[str, Any]:
    if not isinstance(request, Mapping):
        raise PaymentRequestHandoffError("payment_request_required")
    if request.get("status") != "OPEN" or request.get("expired") is True:
        raise PaymentRequestHandoffError("payment_request_not_payable")
    if request.get("payable") is not True:
        raise PaymentRequestHandoffError("payment_request_not_payable")
    if request.get("recipient_approval_required") is not True:
        raise PaymentRequestHandoffError("recipient_approval_requirement_missing")
    if request.get("creates_debt") is not False:
        raise PaymentRequestHandoffError("payment_request_debt_boundary_invalid")
    if not isinstance(payer_account, sika_account_engine.BankAccount):
        raise PaymentRequestHandoffError("payer_account_required")

    payment_id_value = _required(payment_id, "payment_id")
    payee_reference = _request_field(request, "payee_reference")
    amount = _request_field(request, "amount")
    currency = _request_field(request, "currency").upper()
    jurisdiction = _request_field(request, "jurisdiction")
    surface = _request_field(request, "surface")
    request_id = _request_field(request, "request_id")

    intent = sika_payment_orchestrator.create_intent(
        payment_id=payment_id_value,
        idempotency_key=_required(idempotency_key, "idempotency_key"),
        payer_account=payer_account,
        payee_reference=payee_reference,
        amount=amount,
        currency=currency,
        jurisdiction=jurisdiction,
    )
    receipt = sika_customer_payment_authority.build_receipt(
        payment_id=payment_id_value,
        payer_account_id=payer_account.account_id,
        payee_reference=payee_reference,
        amount=amount,
        currency=currency,
        jurisdiction=jurisdiction,
        authority_reference=_required(authority_reference, "authority_reference"),
        authorised_at=_required(authorised_at, "authorised_at"),
        expires_at=_required(expires_at, "expires_at"),
    )

    return {
        "request_id": request_id,
        "surface": surface,
        "payment_intent": intent.as_dict(),
        "customer_authority_receipt": receipt,
        "request_binding": {
            "payment_id": payment_id_value,
            "payer_account_id": payer_account.account_id,
            "payee_reference": payee_reference,
            "amount": amount,
            "currency": currency,
            "jurisdiction": jurisdiction,
        },
        "ready_for_rights_gate": True,
        "ready_for_sika_pay_gateway": False,
        "review_transition_performed": False,
        "authorised_transition_performed": False,
        "provider_calling": False,
        "settlement_execution": False,
        "money_movement": False,
        "human_authority_final": True,
    }


def verify_binding(*, handoff: object, request: object) -> dict[str, Any]:
    if not isinstance(handoff, Mapping) or not isinstance(request, Mapping):
        return {"verified": False, "reason": "handoff_or_request_invalid"}
    binding = handoff.get("request_binding")
    if not isinstance(binding, Mapping):
        return {"verified": False, "reason": "request_binding_missing"}
    fields = ("payee_reference", "amount", "currency", "jurisdiction")
    for field in fields:
        expected = str(request.get(field) or "")
        actual = str(binding.get(field) or "")
        if field == "currency":
            expected = expected.upper()
        if actual != expected:
            return {"verified": False, "reason": f"request_binding_mismatch:{field}"}
    return {
        "verified": True,
        "reason": None,
        "ready_for_rights_gate": True,
        "ready_for_sika_pay_gateway": False,
        "money_movement": False,
    }


def status() -> dict[str, object]:
    return {
        "system": "OAP Pay Request Handoff",
        "first_party": True,
        "binds_open_request_to_payer": True,
        "creates_draft_payment_intent": True,
        "creates_customer_authority_receipt": True,
        "rights_gate_required_next": True,
        "sika_pay_gateway_required_next": True,
        "direct_authorisation": False,
        "provider_calling": False,
        "settlement_execution": False,
        "money_movement": False,
        "human_authority_final": True,
    }
