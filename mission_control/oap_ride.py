"""First-party OAP Ride digital coordination core.

Software-only state machine for connecting rider requests with eligible drivers.
No physical dispatch, vehicle control, payment movement or external provider calls.
"""
from __future__ import annotations

from collections.abc import Mapping
from uuid import UUID, uuid4

RIDE_STATES = (
    "REQUESTED", "MATCH_PROPOSED", "OFFERED", "ACCEPTED",
    "PICKUP_VERIFIED", "JOURNEY_ACTIVE", "COMPLETED", "CANCELLED",
)

def _uuid(value: object, name: str) -> str:
    try:
        return str(UUID(str(value)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError(f"invalid_{name}") from exc

def create_request(*, rider_id: object, pickup: str, destination: str, accessibility: str = "") -> dict[str, object]:
    if not isinstance(pickup, str) or not pickup.strip():
        raise ValueError("invalid_pickup")
    if not isinstance(destination, str) or not destination.strip():
        raise ValueError("invalid_destination")
    return {
        "journey_id": str(uuid4()),
        "rider_id": _uuid(rider_id, "rider_id"),
        "pickup": pickup.strip()[:240],
        "destination": destination.strip()[:240],
        "accessibility": accessibility.strip()[:160] if isinstance(accessibility, str) else "",
        "state": "REQUESTED",
        "physical_dispatch_performed": False,
        "payment_moved": False,
    }

def driver_availability(*, driver_id: object, active: bool, area: str, vehicle_class: str) -> dict[str, object]:
    if type(active) is not bool:
        raise ValueError("invalid_active_state")
    if not isinstance(area, str) or not area.strip():
        raise ValueError("invalid_area")
    if not isinstance(vehicle_class, str) or not vehicle_class.strip():
        raise ValueError("invalid_vehicle_class")
    return {
        "driver_id": _uuid(driver_id, "driver_id"),
        "active": active,
        "area": area.strip()[:120],
        "vehicle_class": vehicle_class.strip()[:80],
        "physical_vehicle_control": False,
    }

def propose_match(*, request: Mapping[str, object], driver: Mapping[str, object]) -> dict[str, object]:
    if request.get("state") != "REQUESTED":
        raise ValueError("request_not_matchable")
    if driver.get("active") is not True:
        raise ValueError("driver_not_active")
    return {
        "match_id": str(uuid4()),
        "journey_id": _uuid(request.get("journey_id"), "journey_id"),
        "rider_id": _uuid(request.get("rider_id"), "rider_id"),
        "driver_id": _uuid(driver.get("driver_id"), "driver_id"),
        "state": "MATCH_PROPOSED",
        "incoming_journey": True,
        "match_reason": "eligible_active_driver",
        "dispatch_performed": False,
    }

def transition(*, journey: Mapping[str, object], to_state: str, journey_code_verified: bool = False) -> dict[str, object]:
    current = journey.get("state")
    allowed = {
        "REQUESTED": {"MATCH_PROPOSED", "CANCELLED"},
        "MATCH_PROPOSED": {"OFFERED", "CANCELLED"},
        "OFFERED": {"ACCEPTED", "CANCELLED"},
        "ACCEPTED": {"PICKUP_VERIFIED", "CANCELLED"},
        "PICKUP_VERIFIED": {"JOURNEY_ACTIVE"},
        "JOURNEY_ACTIVE": {"COMPLETED"},
        "COMPLETED": set(),
        "CANCELLED": set(),
    }
    if current not in allowed or to_state not in allowed[current]:
        raise ValueError("invalid_ride_transition")
    if to_state == "PICKUP_VERIFIED" and journey_code_verified is not True:
        raise ValueError("journey_code_required")
    result = dict(journey)
    result["state"] = to_state
    result["journey_code_verified"] = bool(journey_code_verified) if to_state == "PICKUP_VERIFIED" else result.get("journey_code_verified", False)
    result["physical_dispatch_performed"] = False
    result["payment_moved"] = False
    return result

def status() -> dict[str, object]:
    return {
        "product": "OAP Ride",
        "scope": "software_and_digital_only",
        "flow": [
            "rider_request", "driver_availability", "oap_match", "journey_offer",
            "accept_decline", "pickup", "journey_code", "journey_start",
            "live_journey_state", "journey_complete", "oap_pay_state",
            "receipt_feedback",
        ],
        "guardian_transport": True,
        "the_link": True,
        "incoming": True,
        "oap_world": True,
        "smi": True,
        "physical_operations_in_scope": False,
    }
