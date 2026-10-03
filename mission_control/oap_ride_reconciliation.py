# ruff: noqa: I001
"""Ride adapter over canonical SIKA runtime reconciliation."""
from __future__ import annotations
from typing import Any
from . import oap_ride_payment_bridge, sika_runtime_reconciliation

def reconcile_ride_payment(
    *,
    booking_id: object,
    journal: object,
    provider_id: object,
    provider_reference: object,
    journal_reference: object,
    amount: object,
    currency: object,
    settlement_status: object,
    evidence_hash: object,
) -> dict[str, Any]:
    projection=oap_ride_payment_bridge.projection(booking_id=booking_id)
    if not projection.get("bound"):
        raise ValueError("ride_payment_not_bound")
    if str(projection.get("payment_status") or "") == "MISSING":
        raise ValueError("ride_payment_intent_missing")
    settlement=sika_runtime_reconciliation.receipt(
        provider_id=provider_id,
        provider_reference=provider_reference,
        journal_reference=journal_reference,
        amount=amount,
        currency=currency,
        settlement_status=settlement_status,
        evidence_hash=evidence_hash,
    )
    result=sika_runtime_reconciliation.reconcile(journal=journal,settlement=settlement)
    payload=result.as_dict()
    payload.update({
        "booking_id":str(booking_id),
        "payment_id":projection.get("payment_id"),
        "ride_payment_bound":True,
        "money_moved_by_ride_adapter":False,
    })
    return payload
