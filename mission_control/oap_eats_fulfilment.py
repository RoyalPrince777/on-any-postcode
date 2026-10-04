"""OAP Eats payment and delivery coordination.

This module binds existing first-party SIKA payment evidence to an Eats order
and creates one retry-safe Movement delivery booking. It never captures money,
settles funds, or externally dispatches a courier.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Any

from . import (
    movement_operations,
    oap_eats_store,
    sika_payment_orchestrator,
    sika_payment_reservations,
)


def bind_payment(*, order_id: object, customer_identity_id: object, payment_id: object) -> dict[str, Any]:
    order = oap_eats_store.STORE.read_order(order_id=order_id, identity_id=customer_identity_id)
    intent = sika_payment_orchestrator.read_intent(payment_id)
    if intent is None:
        raise ValueError("payment_intent_not_found")
    hold = sika_payment_reservations.read_hold(payment_id)
    if hold is None or not hold.active:
        raise ValueError("active_payment_hold_required")
    expected = Decimal(order["amount_minor"]) / Decimal("100")
    if intent.amount != expected or hold.amount != expected:
        raise ValueError("payment_amount_mismatch")
    if intent.currency != order["currency"] or hold.currency != order["currency"]:
        raise ValueError("payment_currency_mismatch")
    if hold.payment_id != intent.payment_id or hold.payer_account_id != intent.payer_account_id:
        raise ValueError("payment_hold_binding_mismatch")
    bound = oap_eats_store.STORE.bind_payment(
        order_id=order_id,
        customer_identity_id=customer_identity_id,
        payment_id=intent.payment_id,
        hold_id=hold.hold_id,
    )
    return {
        **bound,
        "payment_status": intent.status,
        "hold_status": hold.status,
        "payment_captured": intent.status == "SETTLED",
        "money_moved_by_eats": False,
    }


def create_delivery(*, order_id: object, customer_identity_id: object, pickup: object,
                    destination: object, idempotency_key: object) -> dict[str, Any]:
    order = oap_eats_store.STORE.read_order(order_id=order_id, identity_id=customer_identity_id)
    if order["fulfilment_mode"] != "delivery":
        raise ValueError("delivery_not_required")
    if order["state"] not in {"authorised", "confirmed", "preparing", "ready", "courier_assigned"}:
        raise ValueError("order_not_ready_for_delivery_booking")
    booking = movement_operations.STORE.create_booking(
        member_identity_id=customer_identity_id,
        service_type="delivery",
        pickup=pickup,
        destination=destination,
        idempotency_key=idempotency_key,
        route_snapshot={"source": "oap_eats", "order_id": str(order_id)},
    )
    bound = oap_eats_store.STORE.bind_movement(
        order_id=order_id,
        customer_identity_id=customer_identity_id,
        booking_id=booking["booking_id"],
    )
    return {
        **bound,
        "movement": booking,
        "courier_dispatched": False,
        "external_dispatch_enabled": False,
    }


def status() -> dict[str, object]:
    return {
        "system": "OAP Eats Fulfilment Bridge",
        "sika_payment_binding": True,
        "active_hold_required": True,
        "amount_currency_match_required": True,
        "movement_delivery_reused": True,
        "movement_booking_idempotency_reused": True,
        "payment_capture_performed": False,
        "external_dispatch_performed": False,
        "money_movement": False,
        "human_authority_final": True,
    }
