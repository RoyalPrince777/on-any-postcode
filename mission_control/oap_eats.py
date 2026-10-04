"""OAP Eats first-party ordering and fulfilment contracts.

This module defines software-only order state, role boundaries, and readiness
truth. It deliberately does not claim live food-business, payment, courier,
or regulatory execution without external evidence.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class EatsOrderState(str, Enum):
    CREATED = "created"
    AUTHORISED = "authorised"
    CONFIRMED = "confirmed"
    PREPARING = "preparing"
    READY = "ready"
    COURIER_ASSIGNED = "courier_assigned"
    COLLECTED = "collected"
    DELIVERED = "delivered"
    SETTLEMENT_PENDING = "settlement_pending"
    SETTLED = "settled"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
    DISPUTED = "disputed"
    FAILED = "failed"


ALLOWED_TRANSITIONS = {
    EatsOrderState.CREATED: {EatsOrderState.AUTHORISED, EatsOrderState.CANCELLED, EatsOrderState.FAILED},
    EatsOrderState.AUTHORISED: {EatsOrderState.CONFIRMED, EatsOrderState.REFUNDED, EatsOrderState.FAILED},
    EatsOrderState.CONFIRMED: {EatsOrderState.PREPARING, EatsOrderState.CANCELLED},
    EatsOrderState.PREPARING: {EatsOrderState.READY, EatsOrderState.CANCELLED},
    EatsOrderState.READY: {EatsOrderState.COURIER_ASSIGNED, EatsOrderState.COLLECTED, EatsOrderState.CANCELLED},
    EatsOrderState.COURIER_ASSIGNED: {EatsOrderState.COLLECTED, EatsOrderState.CANCELLED},
    EatsOrderState.COLLECTED: {EatsOrderState.DELIVERED, EatsOrderState.DISPUTED},
    EatsOrderState.DELIVERED: {EatsOrderState.SETTLEMENT_PENDING, EatsOrderState.DISPUTED},
    EatsOrderState.SETTLEMENT_PENDING: {EatsOrderState.SETTLED, EatsOrderState.DISPUTED},
    EatsOrderState.SETTLED: {EatsOrderState.DISPUTED},
    EatsOrderState.CANCELLED: {EatsOrderState.REFUNDED},
    EatsOrderState.REFUNDED: set(),
    EatsOrderState.DISPUTED: {EatsOrderState.REFUNDED, EatsOrderState.SETTLED},
    EatsOrderState.FAILED: set(),
}


@dataclass(frozen=True)
class EatsRole:
    name: str
    permissions: tuple[str, ...]


ROLES = {
    "customer": EatsRole("customer", ("browse", "basket", "order", "receipt", "dispute")),
    "merchant": EatsRole("merchant", ("catalogue", "availability", "accept_order", "prepare", "handover")),
    "courier": EatsRole("courier", ("see_eligible_jobs", "accept_job", "collect", "deliver")),
}


def can_transition(current: str, target: str) -> bool:
    try:
        source = EatsOrderState(current)
        destination = EatsOrderState(target)
    except ValueError:
        return False
    return destination in ALLOWED_TRANSITIONS[source]


def status() -> dict[str, object]:
    return {
        "product": "OAP Eats",
        "front_door": "/eats",
        "architecture": "OAP World -> Eats -> Merchant -> Order -> Rides movement -> SIKA -> Receipt",
        "first_party_surface": True,
        "shared_systems": [
            "oap_world",
            "my_card",
            "sika",
            "incoming",
            "guardian",
            "oap_data",
            "oap_market",
            "oap_rides",
        ],
        "roles": {key: list(role.permissions) for key, role in ROLES.items()},
        "order_states": [state.value for state in EatsOrderState],
        "courier_engine": "oap_rides_movement",
        "duplicate_map_stack": False,
        "duplicate_payment_stack": False,
        "software_contract_ready": True,
        "live_food_operations_authorised": False,
        "live_payment_execution_authorised": False,
        "live_courier_execution_authorised": False,
        "truth_boundary": (
            "Software contracts are installed. Real merchant trading, food compliance, "
            "payment settlement and courier execution require separately verified live evidence."
        ),
        "human_authority_final": True,
    }
