"""Non-executing first-party SIKA cash service-point intent validation.

No cash receipt, physical location, payment, journal or balance is created here.
All financial execution remains under the existing governed SIKA rails.
"""
from __future__ import annotations

from decimal import Decimal, InvalidOperation


class CashServicePointError(ValueError):
    """Invalid or unapproved service-point cash intent."""


def _required(value: object, field: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise CashServicePointError(f"{field}_required")
    return text


def _amount(value: object) -> str:
    try:
        decimal = Decimal(str(value))
        if not decimal.is_finite() or decimal <= 0:
            raise CashServicePointError("cash_amount_invalid")
        cents = decimal.quantize(Decimal("0.01"))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise CashServicePointError("cash_amount_invalid") from exc
    if cents != decimal or cents <= 0:
        raise CashServicePointError("cash_amount_invalid")
    return f"{cents:.2f}"


def assess_intent(
    *,
    intent_id: object,
    service_point_id: object,
    operator_id: object,
    customer_reference: object,
    amount: object,
    currency: object,
    direction: object,
    staff_authorised: bool = False,
    site_verified: bool = False,
    regulated_cash_authority_proven: bool = False,
) -> dict[str, object]:
    """Validate cash intent but never accept, dispense or post funds."""
    identifiers = {
        "intent_id": _required(intent_id, "intent_id"),
        "service_point_id": _required(service_point_id, "service_point_id"),
        "operator_id": _required(operator_id, "operator_id"),
        "customer_reference": _required(customer_reference, "customer_reference"),
    }
    value = _amount(amount)
    code = _required(currency, "currency").upper()
    if code != "GBP":
        raise CashServicePointError("cash_currency_unsupported")
    kind = _required(direction, "direction").upper()
    if kind not in {"CASH_IN", "CASH_OUT"}:
        raise CashServicePointError("cash_direction_invalid")
    if staff_authorised is not True:
        raise CashServicePointError("cash_staff_authority_missing")
    if site_verified is not True:
        raise CashServicePointError("cash_site_unverified")
    if regulated_cash_authority_proven is not True:
        raise CashServicePointError("cash_regulatory_authority_missing")
    return {
        **identifiers,
        "amount": value,
        "currency": code,
        "direction": kind,
        "intent_validated": True,
        "cash_execution_enabled": False,
        "cash_received": False,
        "cash_dispensed": False,
        "ledger_posted": False,
        "funds_moved": False,
        "receipt_issued": False,
        "human_authority_final": True,
    }


def status() -> dict[str, object]:
    """Static capability truth; never infer cash acceptance from code presence."""
    return {
        "cash_intent_validation_available": True,
        "service_point_registration_enabled": False,
        "cash_in_enabled": False,
        "cash_out_enabled": False,
        "ledger_posting_enabled": False,
        "physical_site_verified": False,
        "regulatory_authority_proven": False,
        "human_authority_final": True,
    }
