"""SIKA closed-loop value boundary.

Models the intended real-money flow without pretending regulated authority exists:
verified GBP-in receipt -> internal SIKA issue -> OAP-internal transfer only.

No bank receipt is trusted merely because a caller says it exists. Production
issuance requires a separately verified regulated settlement receipt.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any


class SikaValueError(ValueError):
    pass


def _money(value: object) -> Decimal:
    try:
        amount = Decimal(str(value)).quantize(Decimal("0.01"))
    except (InvalidOperation, ValueError) as exc:
        raise SikaValueError("invalid_amount") from exc
    if amount <= 0:
        raise SikaValueError("amount_must_be_positive")
    return amount


@dataclass(frozen=True)
class InboundReceipt:
    receipt_id: str
    gbp_amount: str
    bank_reference: str
    settlement_verified: bool = False
    safeguarding_or_partner_evidence: bool = False
    regulatory_basis_verified: bool = False


def issue_from_gbp(receipt: InboundReceipt) -> dict[str, Any]:
    amount = _money(receipt.gbp_amount)
    controls = {
        "settlement_verified": receipt.settlement_verified is True,
        "safeguarding_or_partner_evidence": receipt.safeguarding_or_partner_evidence is True,
        "regulatory_basis_verified": receipt.regulatory_basis_verified is True,
    }
    authorised = all(controls.values())
    return {
        "receipt_id": receipt.receipt_id,
        "bank_reference": receipt.bank_reference,
        "gbp_received": f"{amount:.2f}",
        "sika_to_issue": f"{amount:.2f}",
        "anchor": "1 SIKA = 1 GBP target",
        "controls": controls,
        "issuance_authorised": authorised,
        "spendable_sika_created": authorised,
        "external_payment_enabled": False,
        "cash_out_enabled": False,
        "reason": "verified_inbound_value_ready" if authorised else "regulated_inbound_evidence_required",
    }


def internal_transfer(amount_sika: object, *, sender_balance_sika: object) -> dict[str, Any]:
    amount = _money(amount_sika)
    balance = Decimal(str(sender_balance_sika)).quantize(Decimal("0.01"))
    sufficient = balance >= amount
    return {
        "amount_sika": f"{amount:.2f}",
        "sender_balance_before": f"{balance:.2f}",
        "sender_balance_after": f"{(balance - amount):.2f}" if sufficient else f"{balance:.2f}",
        "receiver_credit_sika": f"{amount:.2f}" if sufficient else "0.00",
        "internal_oap_only": True,
        "sufficient_balance": sufficient,
        "transfer_allowed": sufficient,
        "bank_transfer_created": False,
        "external_payment_created": False,
        "cash_out_created": False,
        "reason": "internal_sika_transfer_allowed" if sufficient else "insufficient_sika",
    }


def model_status() -> dict[str, Any]:
    return {
        "real_money_entry": "regulated_bank_or_payment_rail",
        "internal_unit": "SIKA",
        "target_anchor": "1 SIKA = 1 GBP",
        "issuance_trigger": "verified settled GBP receipt only",
        "usage_scope": "OAP internal only",
        "internal_transfer_supported": True,
        "external_transfer_supported": False,
        "cash_out_supported": False,
        "payment_initiation_supported": False,
        "customer_funds_claim": False,
        "regulatory_gate_required": True,
    }
