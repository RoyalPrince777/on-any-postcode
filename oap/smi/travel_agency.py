"""OAP Travel Agency truth/status composition.

OAP Travel composes the reusable Intelligence Capability Registry, first-party
Booking Core and first-party Supply Core. External services are optional lookup
sources only; they are not OAP partners and are not persisted as OAP inventory.
"""
from __future__ import annotations

from typing import Any

from . import (
    booking_orchestrator,
    intelligence_capability_registry,
    supply_integration,
    supply_source_policy,
)

TRAVEL_AGENCY_REVISION = "2026-09-04-v6"


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
    external_lookup = supply_integration.status()
    booking_core = booking_orchestrator.status()
    direct_supply = _direct_supply_status()
    source_policy = supply_source_policy.status()

    direct_live = bool(direct_supply["live_direct_supply"])
    booking_live = bool(direct_supply["direct_booking_runtime_ready"])
    payment_live = bool(direct_supply["payment_capture_live"])
    commission_live = bool(direct_supply["commission_settlement_live"])

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
            "id": "supplier_independence_policy",
            "ready": bool(source_policy["policy_ready"]),
            "required_for": "external_lookup_optional_and_oap_direct_preference",
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
            "id": "external_lookup_framework",
            "ready": bool(external_lookup["adapter_framework_ready"]),
            "required_for": "optional_on_demand_reference_search",
        },
        {
            "id": "live_direct_supply",
            "ready": direct_live,
            "required_for": "current_oap_availability_and_pricing_claims",
        },
        {
            "id": "booking_execution",
            "ready": booking_live,
            "required_for": "oap_direct_reservation_transactions",
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
        dict.fromkeys((*external_lookup["supported_categories"], *direct_categories))
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
        "supplier_independence_policy_ready": source_policy["policy_ready"],
        "oap_supply_core_software_ready": direct_supply["software_ready"],
        "oap_supply_core_schema_ready": direct_supply["schema_ready"],
        "partner_supply_schema_ready": False,
        "oap_owns_booking_experience": True,
        "oap_owns_supplier_inventory": False,
        "oap_owns_direct_supplier_inventory_system": True,
        "oap_owns_external_supplier_inventory": False,
        "oap_direct_preferred_when_comparable": source_policy[
            "oap_direct_preferred_when_comparable"
        ],
        "external_suppliers_optional": True,
        "single_external_provider_dependency_allowed": False,
        "booking_com_required": False,
        "booking_com_partner": False,
        "preferred_supply_source_order": ("oap_direct",),
        "supply_adapter_framework_ready": external_lookup["adapter_framework_ready"],
        "external_lookup_mode": "on_demand_only",
        "external_lookup_persisted": False,
        "live_supply_search_ready": direct_live,
        "external_live_supply_ready": False,
        "runtime_external_search_ready": bool(
            external_lookup["live_search_provider_count"]
        ),
        "partner_snapshot_supply_ready": False,
        "active_partner_snapshot_count": 0,
        "live_partner_offer_count": 0,
        "direct_live_supply_ready": direct_live,
        "live_inventory_survives_external_provider_loss": direct_live,
        "architecture_survives_external_provider_loss": bool(
            source_policy["policy_ready"] and direct_supply["software_ready"]
        ),
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
        "external_provider_count": external_lookup["provider_count"],
        "runtime_connected_external_provider_count": external_lookup[
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
            "system, while suppliers retain ownership of their underlying inventory. "
            "External travel services are optional on-demand lookup references only: "
            "they are not OAP partners, their offers are not persisted as OAP supply, "
            "and OAP booking does not hand execution to them. A live reservation, payment, "
            "Pass or commission is claimed only when its governed runtime evidence exists."
        ),
    }
