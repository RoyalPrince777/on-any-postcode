"""SIKA commerce boundary.

Turns an existing OAP Commerce order into a canonical SIKA settlement intent
without issuing e-money, storing customer funds, or executing a payment.

The monetary execution boundary remains with an authorised payment/e-money
provider when one is connected and approved.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Any
from uuid import UUID

from . import postgres_db
from .sika_global import SIKA_CODE, SIKA_TO_GBP


class SikaCommerceUnavailable(RuntimeError):
    """Raised when SIKA commerce state cannot be read safely."""


def _uuid(value: object, code: str) -> str:
    try:
        return str(UUID(str(value)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError(code) from exc


def settlement_intent(*, order_id: object) -> dict[str, Any]:
    """Return a deterministic SIKA representation of an existing GBP order.

    This is an accounting/checkout intent only. It never debits a wallet,
    captures a card, transfers funds, redeems SIKA, or marks an order paid.
    """

    order = _uuid(order_id, "invalid_order_id")
    try:
        with postgres_db.connect(readonly=True) as connection:
            row = connection.execute(
                """SELECT o.order_id,o.state,o.currency,o.subtotal_minor,
                          p.intent_id,p.state,p.amount_minor,p.currency,
                          p.provider_reference
                   FROM oap_commerce_orders o
                   LEFT JOIN oap_commerce_payment_intents p
                     ON p.order_id=o.order_id
                   WHERE o.order_id=%s
                   LIMIT 1""",
                (order,),
            ).fetchone()
    except Exception as exc:
        raise SikaCommerceUnavailable("sika_commerce_read_failed") from exc

    if row is None:
        return {
            "order_id": order,
            "ready": False,
            "reason": "order_missing",
            "payment_execution_enabled": False,
            "customer_funds_held": False,
        }

    currency = str(row[2] or "").upper()
    if currency != "GBP":
        return {
            "order_id": order,
            "ready": False,
            "reason": "gbp_anchor_required",
            "order_currency": currency,
            "payment_execution_enabled": False,
            "customer_funds_held": False,
        }

    subtotal_minor = int(row[3])
    amount_sika = (Decimal(subtotal_minor) / Decimal(100)) / SIKA_TO_GBP
    payment_present = row[4] is not None
    payment_matches = (
        payment_present
        and int(row[6]) == subtotal_minor
        and str(row[7] or "").upper() == "GBP"
    )

    return {
        "order_id": str(row[0]),
        "order_state": str(row[1]),
        "order_currency": currency,
        "subtotal_minor": subtotal_minor,
        "canonical_unit": SIKA_CODE,
        "amount_sika": f"{amount_sika:.2f}",
        "anchor": "1 SIKA = 1 GBP",
        "payment_intent_id": str(row[4]) if row[4] else None,
        "payment_intent_state": str(row[5]) if row[5] else None,
        "payment_intent_matches_order": payment_matches,
        "ready": payment_matches,
        "settlement_provider_required": True,
        "provider_reference": str(row[8]) if row[8] else None,
        "payment_execution_enabled": False,
        "customer_funds_held": False,
        "wallet_debit_performed": False,
        "sika_issued": False,
        "sika_redeemed": False,
        "money_transfer_performed": False,
        "human_authority_final": True,
    }


def status() -> dict[str, object]:
    return {
        "component": "SIKA Commerce",
        "canonical_unit": SIKA_CODE,
        "anchor": "1 SIKA = 1 GBP",
        "commerce_intents_enabled": True,
        "provider_handoff_boundary_enabled": True,
        "payment_execution_enabled": False,
        "customer_funds_enabled": False,
        "wallet_money_enabled": False,
        "sika_issuance_enabled": False,
        "sika_redemption_enabled": False,
        "regulated_provider_required": True,
        "human_authority_final": True,
    }
