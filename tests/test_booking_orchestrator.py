from datetime import UTC, datetime

import pytest

from oap.smi import booking_orchestrator, travel_agency


def _external_offer():
    return {
        "provider_id": "booking_com",
        "category": "stay",
        "source_offer_id": "external-stay-1",
        "title": "External Stay",
        "place_label": "London",
        "availability_state": "available",
        "observed_at": datetime.now(UTC).isoformat(),
        "source_url": "https://example.com/stay/1",
        "currency": "GBP",
        "total_price": 240.0,
        "price_basis": "2 nights total",
    }


def test_external_marketplace_offer_cannot_create_oap_booking_intent():
    with pytest.raises(ValueError, match="unknown_supply_provider"):
        booking_orchestrator.prepare_booking_intent(_external_offer())


def test_booking_core_remains_first_party_and_fail_closed():
    booking = booking_orchestrator.status()
    agency = travel_agency.status()

    assert booking["first_party_booking_orchestration_ready"] is True
    assert booking["owns_booking_experience"] is True
    assert booking["owns_supplier_inventory"] is False
    assert booking["direct_booking_execution_ready"] is False
    assert booking["payment_execution_ready"] is False
    assert booking["creates_intelligence_worlds"] is False
    assert booking["creates_agents"] is False
    assert booking["creates_brain"] is False
    assert booking["external_provider_authority"] is False

    assert agency["oap_booking_core_ready"] is True
    assert agency["oap_owns_booking_experience"] is True
    assert agency["oap_owns_supplier_inventory"] is False
    assert agency["external_provider_count"] == 0
    assert agency["external_supplier_catalogue_allowed"] is False
    assert agency["external_data_fetch_allowed"] is True
    assert agency["payment_transactions_live"] is False
