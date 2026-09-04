"""OAP Travel Agency truth/status composition.

This is not a separate Intelligence World or SMI brain. It composes the reusable
Intelligence Capability Registry, first-party OAP Booking Core, first-party OAP
Supply Core and replaceable external supply adapters. External suppliers never
become OAP authority.
"""
from __future__ import annotations

from typing import Any

from . import booking_orchestrator, intelligence_capability_registry, supply_integration

TRAVEL_AGENCY_REVISION = "2026-09-04-v3"


def _direct_supply_status() -> dict[str, Any]:
    """Read first-party supply readiness without making SMI depend on DB startup."""

    try:
        from mission_control import travel_supply_core

        return travel_supply_core.status()
    except Exception:  # noqa: BLE001
        return {
            "software_ready": False,
            "schema_ready": False,
            "certified_supplier_count": 0,
            "active_listing_count": 0,
            "live_inventory_slot_count": 0,
            "confirmed_reservation_count": 0,
            "live_direct_supply": False,
            "direct_booking_runtime_ready": False,
            "payment_capture_live": False,
            "pass_issuance_live": False,
            "commission_settlement_live": False,
            "human_authority_final": True,
        }


def status() -> dict[str, Any]:
    registry = intelligence_capability_registry.status()
    external_supply = supply_integration.status()
    booking_core = booking_orchestrator.status()
    direct_supply = _direct_supply_status()

    external_live = bool(external_supply["live_supply_connected"])
    direct_live = bool(direct_supply["live_direct_supply"])
    live_supply = external_live or direct_live
    external_booking = bool(external_supply["booking_transactions_live"])
    direct_booking = bool(direct_supply["direct_booking_runtime_ready"])
    booking_live = external_booking or direct_booking
    payment_live = bool(
        external_supply["payment_transactions_live"]
        or direct_supply["payment_capture_live"]
    )
    commission_live = bool(
        external_supply["commission_settlement_live"]
        or direct_supply["commission_settlement_live"]
    )

    gates = (
        {
            "id": "capability_registry",
            "ready": bool(registry["registry_software_ready"]),
            "required_for": "all_travel_intelligence",
        },
        {
            "id": "oap_booking_core",
            "ready": bool(booking_core["first_party_booking_orchestration_ready"]),
            "required_for": "oap_owned_booking_journey_and_human_confirmation",
        },
        {
            "id": "oap_supply_core_software",
            "ready": bool(direct_supply["software_ready"]),
            "required_for": "first_party_supplier_inventory_and_reservation_logic",
        },
        {
            "id": "oap_supply_core_schema",
            "ready": bool(direct_supply["schema_ready"]),
            "required_for": "durable_direct_supplier_inventory",
        },
        {
            "id": "supply_adapter_framework",
            "ready": bool(external_supply["adapter_framework_ready"]),
            "required_for": "replaceable_external_supplier_normalisation",
        },
        {
            "id": "live_supply_search",
            "ready": live_supply,
            "required_for": "current_availability_and_pricing_claims",
        },
        {
            "id": "booking_execution",
            "ready": booking_live,
            "required_for": "reservation_transactions_with_live_supply",
        },
        {
            "id": "payment_execution",
            "ready": payment_live,
            "required_for": "payment_capture_or_settlement",
        },
        {
            "id": "commission_settlement",
            "ready": commission_live,
            "required_for": "real_supplier_commission_revenue",
        },
    )

    direct_categories = (
        "stay",
        "attraction",
        "activity",
        "car_rental",
        "transport",
        "event",
    )
    supported_categories = tuple(
        dict.fromkeys((*external_supply["supported_categories"], *direct_categories))
    )

    return {
        "component": "OAP Travel Agency",
        "revision": TRAVEL_AGENCY_REVISION,
        "kind": "commercial_orchestration_product_capability",
        "intelligence_world": False,
        "agent": False,
        "brain": False,
        "brain_count_added": 0,
        "capability_registry_ready": registry["registry_software_ready"],
        "oap_booking_core_ready": booking_core["first_party_booking_orchestration_ready"],
        "oap_supply_core_software_ready": direct_supply["software_ready"],
        "oap_supply_core_schema_ready": direct_supply["schema_ready"],
        "oap_owns_booking_experience": True,
        "oap_owns_supplier_inventory": False,
        "oap_owns_direct_supplier_inventory_system": True,
        "oap_owns_external_supplier_inventory": False,
        "supply_adapter_framework_ready": external_supply["adapter_framework_ready"],
        "live_supply_search_ready": live_supply,
        "external_live_supply_ready": external_live,
        "direct_live_supply_ready": direct_live,
        "booking_transactions_live": booking_live,
        "payment_transactions_live": payment_live,
        "pass_issuance_live": bool(direct_supply["pass_issuance_live"]),
        "commission_settlement_live": commission_live,
        "certified_direct_supplier_count": direct_supply["certified_supplier_count"],
        "active_direct_listing_count": direct_supply["active_listing_count"],
        "live_direct_inventory_slot_count": direct_supply["live_inventory_slot_count"],
        "confirmed_direct_reservation_count": direct_supply[
            "confirmed_reservation_count"
        ],
        "commercial_journey": registry["commercial_journey"],
        "supported_supply_categories": supported_categories,
        "external_provider_count": external_supply["provider_count"],
        "runtime_connected_external_provider_count": external_supply[
            "runtime_connected_count"
        ],
        "gates": gates,
        "allowed_revenue_models": (
            "disclosed_supplier_commission",
            "disclosed_service_fee",
            "disclosed_booking_fee_where_legal",
        ),
        "hidden_fees_allowed": False,
        "provider_authority": False,
        "guardian_gate_required": True,
        "human_authority_final": True,
        "production_booking_claim_allowed": booking_live,
        "production_payment_claim_allowed": payment_live,
        "production_commission_claim_allowed": commission_live,
        "truth_boundary": (
            "OAP owns its booking experience and first-party direct-supplier inventory "
            "system, but suppliers retain ownership of their underlying inventory. External "
            "providers remain optional supply sources. A live availability, reservation, "
            "captured payment, issued Pass or earned commission may only be claimed when "
            "its corresponding governed runtime evidence is present."
        ),
    }
