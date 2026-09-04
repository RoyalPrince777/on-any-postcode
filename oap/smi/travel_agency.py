"""OAP Travel Agency truth/status composition.

OAP Travel is built on first-party Booking Core + OAP Supply Core. External
marketplace data can be fetched as research context, but no external marketplace
is part of the OAP catalogue or reservation path unless it later joins directly
as a Certified OAP Supplier under a separate governed process.
"""
from __future__ import annotations

from typing import Any

from . import booking_orchestrator, intelligence_capability_registry, supply_integration, supply_source_policy

TRAVEL_AGENCY_REVISION = "2026-09-04-v6"


def _direct_supply_status() -> dict[str, Any]:
    try:
        from mission_control import listing_media, travel_supply_core

        result = travel_supply_core.status()
        result["listing_media"] = listing_media.status()
        return result
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
            "listing_media": {"schema_ready": False, "photo_count": 0},
            "human_authority_final": True,
        }


def status() -> dict[str, Any]:
    registry = intelligence_capability_registry.status()
    external_data = supply_integration.status()
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
            "id": "oap_direct_policy",
            "ready": bool(source_policy["policy_ready"]),
            "required_for": "direct_supplier_catalogue_and_external_data_separation",
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
            "id": "listing_photo_store",
            "ready": bool(direct_supply["listing_media"]["schema_ready"]),
            "required_for": "first_party_listing_images",
        },
        {
            "id": "live_direct_supply",
            "ready": direct_live,
            "required_for": "current_oap_availability_and_pricing",
        },
        {
            "id": "booking_execution",
            "ready": booking_live,
            "required_for": "reservation_transactions_with_live_direct_supply",
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
        "listing_photo_schema_ready": direct_supply["listing_media"]["schema_ready"],
        "listing_photo_count": direct_supply["listing_media"]["photo_count"],
        "oap_owns_booking_experience": True,
        "oap_owns_supplier_inventory": False,
        "oap_owns_direct_supplier_inventory_system": True,
        "oap_owns_external_supplier_inventory": False,
        "oap_direct_preferred_when_comparable": True,
        "external_supplier_catalogue_allowed": False,
        "external_data_fetch_allowed": True,
        "external_data_is_research_only": True,
        "single_external_provider_dependency_allowed": False,
        "preferred_supply_source_order": source_policy["preferred_source_order"],
        "supply_adapter_framework_ready": external_data["adapter_framework_ready"],
        "live_supply_search_ready": direct_live,
        "external_live_supply_ready": False,
        "runtime_external_search_ready": False,
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
        "confirmed_direct_reservation_count": direct_supply["confirmed_reservation_count"],
        "commercial_journey": registry["commercial_journey"],
        "supported_supply_categories": direct_categories,
        "external_provider_count": 0,
        "runtime_connected_external_provider_count": 0,
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
            "OAP owns the booking experience and first-party direct-supplier marketplace. "
            "Only directly onboarded Certified OAP Suppliers enter the OAP catalogue. "
            "External marketplace information may be fetched for research/comparison but "
            "is not Partner Supply, OAP inventory, a reservation source or payment authority."
        ),
    }
