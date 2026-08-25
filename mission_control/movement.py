"""Canonical public model for OAP Movement and provider-ready eSIM connectivity.

This module defines the product boundary for passenger rides, e-bikes, delivery,
booking, tracking, driver/rider roles and managed device connectivity. It does
not dispatch real-world work, charge money or activate carrier profiles.
Those operations stay fail-closed until approved providers, identity checks,
compliance and Human Authority gates are connected.
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
        "status": "Provider required",
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
        "status": "Operator required",
    },
    {
        "id": "booking",
        "name": "Booking",
        "icon": "📅",
        "purpose": "Plan a ride, e-bike or delivery for now or a future time.",
        "status": "Draft planning only",
    },
    {
        "id": "tracking",
        "name": "Track",
        "icon": "📍",
        "purpose": "Follow an approved journey or delivery without exposing private location publicly.",
        "status": "Provider required",
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
            "purpose": "Expose coarse connected/offline readiness for approved devices without publishing precise network identity.",
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

MOVEMENT_SAFEGUARDS: tuple[str, ...] = (
    "Identity and role certification before driver, rider, courier or merchant work.",
    "Transport, insurance, licensing and local legal checks before real dispatch.",
    "Explicit user consent before live location sharing.",
    "No public exposure of eSIM carrier identifiers, activation data or precise device location.",
    "No autonomous eSIM activation, deactivation or carrier switching.",
    "No autonomous passenger or delivery dispatch; Human Authority remains final for governed execution policy.",
    "Payments remain separate until an approved compliant payment provider is connected.",
    "Link Up can carry protected trip communication without exposing private phone numbers.",
)

EXECUTION_BOUNDARY: dict[str, bool] = {
    "booking_draft_enabled": True,
    "booking_persistence_enabled": False,
    "dispatch_enabled": False,
    "payment_enabled": False,
    "live_tracking_enabled": False,
    "esim_activation_enabled": False,
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
    """Validate unique services/roles and fail-closed real-world controls."""

    service_duplicates = _duplicate_ids(MOVEMENT_SERVICES)
    role_duplicates = _duplicate_ids(MOVEMENT_ROLES)
    provider_controls = ESIM_CONNECTIVITY["provider_controls"]

    privileged_flags = {
        "dispatch_enabled": EXECUTION_BOUNDARY["dispatch_enabled"],
        "payment_enabled": EXECUTION_BOUNDARY["payment_enabled"],
        "live_tracking_enabled": EXECUTION_BOUNDARY["live_tracking_enabled"],
        "esim_activation_enabled": EXECUTION_BOUNDARY["esim_activation_enabled"],
        "profile_activation_enabled": provider_controls["profile_activation_enabled"],
        "profile_deactivation_enabled": provider_controls["profile_deactivation_enabled"],
        "carrier_switch_enabled": provider_controls["carrier_switch_enabled"],
        "remote_profile_install_enabled": provider_controls[
            "remote_profile_install_enabled"
        ],
    }

    errors: list[str] = []
    if service_duplicates:
        errors.append(
            "Duplicate Movement service IDs: " + ", ".join(sorted(service_duplicates))
        )
    if role_duplicates:
        errors.append(
            "Duplicate Movement role IDs: " + ", ".join(sorted(role_duplicates))
        )
    if any(privileged_flags.values()):
        errors.append("Real-world Movement and eSIM controls must remain fail-closed")
    if not EXECUTION_BOUNDARY["human_approval_required"]:
        errors.append("Human approval must remain required")

    return {
        "passed": not errors,
        "errors": errors,
        "checks": {
            "services": len(MOVEMENT_SERVICES),
            "roles": len(MOVEMENT_ROLES),
            "duplicate_service_ids": len(service_duplicates),
            "duplicate_role_ids": len(role_duplicates),
            "privileged_controls_enabled": sum(privileged_flags.values()),
            "provider_connected": bool(provider_controls["provider_connected"]),
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
    """Return coarse readiness only; never expose carrier/device identifiers."""

    validation = validate_movement_architecture()
    return {
        "product": "OAP Movement",
        "architecture_passed": validation["passed"],
        "services": len(MOVEMENT_SERVICES),
        "roles": len(MOVEMENT_ROLES),
        "esim_provider_connected": False,
        "dispatch_enabled": EXECUTION_BOUNDARY["dispatch_enabled"],
        "payment_enabled": EXECUTION_BOUNDARY["payment_enabled"],
        "live_tracking_enabled": EXECUTION_BOUNDARY["live_tracking_enabled"],
        "esim_activation_enabled": EXECUTION_BOUNDARY["esim_activation_enabled"],
        "human_approval_required": EXECUTION_BOUNDARY["human_approval_required"],
    }
