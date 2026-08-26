"""Canonical public model for OAP Movement and managed connectivity.

Movement presents passenger rides, e-bikes, delivery, booking and tracking while
keeping consequential execution behind provider, compliance and human gates.
The public projection reports coarse capability readiness only; private booking,
worker, location, payment and carrier data never appears here.
"""
from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

MOVEMENT_SERVICES: tuple[dict[str, str], ...] = (
    {
        "id": "ride",
        "name": "OAP Ride",
        "icon": "🚗",
        "purpose": "Passenger journeys with pickup, destination and governed driver matching.",
        "status": "Operations foundation ready",
    },
    {
        "id": "ebike",
        "name": "OAP E-Bike",
        "icon": "🚲",
        "purpose": "Reserve connected e-bikes with battery, range, pickup and return awareness.",
        "status": "Fleet provider required",
    },
    {
        "id": "delivery",
        "name": "OAP Delivery",
        "icon": "📦",
        "purpose": "Collection and delivery for parcels, shopping, food and local merchants.",
        "status": "Operations foundation ready",
    },
    {
        "id": "booking",
        "name": "Booking",
        "icon": "📅",
        "purpose": "Plan a ride, e-bike or delivery for now or a future time.",
        "status": "Durable schema required",
    },
    {
        "id": "tracking",
        "name": "Track",
        "icon": "📍",
        "purpose": "Share a journey location only with explicit participant consent.",
        "status": "Private consent boundary ready",
    },
)

MOVEMENT_ROLES: tuple[dict[str, str], ...] = (
    {
        "id": "member",
        "name": "Member",
        "purpose": "Books a ride, e-bike or delivery after identity and service checks.",
    },
    {
        "id": "driver",
        "name": "Driver",
        "purpose": "Carries passengers in an approved, insured and compliant vehicle.",
    },
    {
        "id": "rider",
        "name": "Rider",
        "purpose": "Uses an approved cycle, e-bike or other permitted vehicle for local jobs.",
    },
    {
        "id": "courier",
        "name": "Courier",
        "purpose": "Collects and delivers approved goods with proof-of-delivery controls.",
    },
    {
        "id": "merchant",
        "name": "Merchant",
        "purpose": "Creates eligible pickup and delivery work for approved local orders.",
    },
)

ESIM_CONNECTIVITY: dict[str, Any] = {
    "name": "OAP eSIM Connectivity",
    "status": "Provider not connected",
    "purpose": (
        "Keep approved driver, rider, courier and fleet devices connected for "
        "navigation, booking, safety and operational messaging."
    ),
    "capabilities": (
        {
            "id": "device-link",
            "name": "Device Link",
            "purpose": "Bind one approved work device to one certified OAP role without exposing carrier identifiers publicly.",
        },
        {
            "id": "data-path",
            "name": "Movement Data",
            "purpose": "Provide a managed data path for maps, jobs, tracking and Link Up communication.",
        },
        {
            "id": "failover",
            "name": "Connectivity Failover",
            "purpose": "Support a provider-controlled backup data path when the primary network is unavailable.",
        },
        {
            "id": "fleet-awareness",
            "name": "Fleet Awareness",
            "purpose": "Expose coarse connected/offline readiness without publishing precise network identity.",
        },
    ),
    "provider_controls": {
        "provider_connected": False,
        "profile_activation_enabled": False,
        "profile_deactivation_enabled": False,
        "carrier_switch_enabled": False,
        "remote_profile_install_enabled": False,
    },
}

MOVEMENT_BUILD_ORDER: tuple[dict[str, str], ...] = (
    {"step": "1", "id": "routing", "name": "Routing provider"},
    {"step": "2", "id": "booking", "name": "Booking persistence"},
    {"step": "3", "id": "availability", "name": "Driver / Rider availability"},
    {"step": "4", "id": "matching", "name": "Governed matching / dispatch"},
    {"step": "5", "id": "tracking", "name": "Consented live tracking"},
    {"step": "6", "id": "esim", "name": "eSIM telecom boundary"},
    {"step": "7", "id": "payments", "name": "Payments"},
    {"step": "8", "id": "linkup", "name": "Link Up trip communications"},
)

MOVEMENT_SAFEGUARDS: tuple[str, ...] = (
    "Identity and role certification before driver, rider, courier or merchant work.",
    "Transport, insurance, licensing and local legal checks before external dispatch.",
    "Explicit participant consent before any live location point is stored.",
    "Tracking points expire with the participant's consent window and are never public.",
    "No public exposure of eSIM carrier identifiers, activation data or precise device location.",
    "No autonomous eSIM activation, deactivation or carrier switching.",
    "Internal match proposals do not equal external fleet dispatch.",
    "Payment intents do not authorize or capture money without an approved provider.",
    "Link Up owns message bodies; Movement stores only a trip-channel binding.",
)

EXECUTION_BOUNDARY: dict[str, bool] = {
    "external_dispatch_enabled": False,
    "payment_capture_enabled": False,
    "esim_activation_enabled": False,
    "carrier_switch_enabled": False,
    "remote_profile_install_enabled": False,
    "public_tracking_enabled": False,
    "human_approval_required": True,
}


def _duplicate_ids(items: Iterable[Mapping[str, Any]]) -> set[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for item in items:
        item_id = str(item.get("id", "")).strip().casefold()
        if item_id in seen:
            duplicates.add(item_id)
        seen.add(item_id)
    return duplicates


def validate_movement_architecture() -> dict[str, Any]:
    """Validate unique services/roles/order and fail-closed external controls."""

    service_duplicates = _duplicate_ids(MOVEMENT_SERVICES)
    role_duplicates = _duplicate_ids(MOVEMENT_ROLES)
    order_duplicates = _duplicate_ids(MOVEMENT_BUILD_ORDER)
    provider_controls = ESIM_CONNECTIVITY["provider_controls"]
    privileged_flags = {
        key: value
        for key, value in EXECUTION_BOUNDARY.items()
        if key != "human_approval_required"
    }
    privileged_flags.update(
        {
            "profile_activation_enabled": provider_controls[
                "profile_activation_enabled"
            ],
            "profile_deactivation_enabled": provider_controls[
                "profile_deactivation_enabled"
            ],
        }
    )

    errors: list[str] = []
    if service_duplicates:
        errors.append(
            "Duplicate Movement service IDs: " + ", ".join(sorted(service_duplicates))
        )
    if role_duplicates:
        errors.append(
            "Duplicate Movement role IDs: " + ", ".join(sorted(role_duplicates))
        )
    if order_duplicates:
        errors.append(
            "Duplicate Movement build IDs: " + ", ".join(sorted(order_duplicates))
        )
    if any(privileged_flags.values()):
        errors.append("External Movement controls must remain fail-closed")
    if not EXECUTION_BOUNDARY["human_approval_required"]:
        errors.append("Human approval must remain required")

    return {
        "passed": not errors,
        "errors": errors,
        "checks": {
            "services": len(MOVEMENT_SERVICES),
            "roles": len(MOVEMENT_ROLES),
            "ordered_steps": len(MOVEMENT_BUILD_ORDER),
            "duplicate_service_ids": len(service_duplicates),
            "duplicate_role_ids": len(role_duplicates),
            "duplicate_order_ids": len(order_duplicates),
            "privileged_controls_enabled": sum(bool(v) for v in privileged_flags.values()),
        },
    }


def get_public_movement() -> dict[str, Any]:
    """Return the non-sensitive public Movement product projection."""

    return {
        "product_name": "OAP Movement",
        "tagline": "Ride. Deliver. Book. Move.",
        "law": "The Spot → Movement → Ride / E-Bike / Delivery",
        "services": tuple(dict(item) for item in MOVEMENT_SERVICES),
        "roles": tuple(dict(item) for item in MOVEMENT_ROLES),
        "build_order": tuple(dict(item) for item in MOVEMENT_BUILD_ORDER),
        "connectivity": {
            "name": ESIM_CONNECTIVITY["name"],
            "status": ESIM_CONNECTIVITY["status"],
            "purpose": ESIM_CONNECTIVITY["purpose"],
            "capabilities": tuple(
                dict(item) for item in ESIM_CONNECTIVITY["capabilities"]
            ),
        },
        "safeguards": MOVEMENT_SAFEGUARDS,
        "execution": dict(EXECUTION_BOUNDARY),
    }


def get_public_movement_status() -> dict[str, Any]:
    """Return coarse capability readiness without private identifiers/data."""

    from . import movement_operations, routing

    validation = validate_movement_architecture()
    schema = movement_operations.movement_schema_status()
    route_state = routing.status()
    schema_ready = bool(schema["schema_ready"])
    return {
        "product": "OAP Movement",
        "architecture_passed": validation["passed"],
        "ordered_steps": len(MOVEMENT_BUILD_ORDER),
        "routing_adapter_configured": bool(route_state["configured"]),
        "routing_runtime_verified": bool(route_state["runtime_verified"]),
        "booking_persistence_ready": schema_ready,
        "availability_store_ready": schema_ready,
        "match_proposal_store_ready": schema_ready,
        "tracking_consent_store_ready": schema_ready,
        "esim_request_store_ready": schema_ready,
        "payment_intent_store_ready": schema_ready,
        "linkup_trip_binding_ready": schema_ready,
        "external_dispatch_enabled": EXECUTION_BOUNDARY[
            "external_dispatch_enabled"
        ],
        "payment_capture_enabled": EXECUTION_BOUNDARY[
            "payment_capture_enabled"
        ],
        "esim_activation_enabled": EXECUTION_BOUNDARY[
            "esim_activation_enabled"
        ],
        "public_tracking_enabled": EXECUTION_BOUNDARY["public_tracking_enabled"],
        "human_approval_required": EXECUTION_BOUNDARY["human_approval_required"],
    }
