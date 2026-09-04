"""OAP Travel Agency truth/status composition.

This is not a separate Intelligence World or SMI brain. It composes the reusable
Intelligence Capability Registry, first-party OAP Booking Core and replaceable
travel-supply adapter layer, exposing truthful commercial readiness without
granting execution authority.
"""

from __future__ import annotations

from typing import Any

from . import booking_orchestrator, intelligence_capability_registry, supply_integration

TRAVEL_AGENCY_REVISION = "2026-09-04-v2"


def status() -> dict[str, Any]:
    registry = intelligence_capability_registry.status()
    supply = supply_integration.status()
    booking_core = booking_orchestrator.status()

    live_supply = bool(supply["live_supply_connected"])
    booking_live = bool(supply["booking_transactions_live"])
    payment_live = bool(supply["payment_transactions_live"])
    commission_live = bool(supply["commission_settlement_live"])

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
            "id": "supply_adapter_framework",
            "ready": bool(supply["adapter_framework_ready"]),
            "required_for": "supplier_normalisation_and_provenance",
        },
        {
            "id": "live_supply_search",
            "ready": live_supply,
            "required_for": "current_availability_and_pricing_claims",
        },
        {
            "id": "booking_execution",
            "ready": booking_live,
            "required_for": "confirmed_reservation_transactions",
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
        "oap_owns_booking_experience": booking_core["owns_booking_experience"],
        "oap_owns_supplier_inventory": booking_core["owns_supplier_inventory"],
        "supply_adapter_framework_ready": supply["adapter_framework_ready"],
        "live_supply_search_ready": live_supply,
        "booking_transactions_live": booking_live,
        "payment_transactions_live": payment_live,
        "commission_settlement_live": commission_live,
        "commercial_journey": registry["commercial_journey"],
        "supported_supply_categories": supply["supported_categories"],
        "provider_count": supply["provider_count"],
        "runtime_connected_provider_count": supply["runtime_connected_count"],
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
            "OAP owns the booking experience, intent state and confirmation journey. "
            "External providers may supply inventory and external booking destinations. "
            "OAP may not claim a live supplier search, confirmed booking, captured payment "
            "or earned commission until the corresponding governed runtime gate is green."
        ),
    }
