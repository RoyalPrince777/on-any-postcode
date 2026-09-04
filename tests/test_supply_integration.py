from datetime import UTC, datetime

import pytest

from oap.smi import supply_integration


def _offer(**overrides):
    payload = {
        "provider_id": "booking_com",
        "category": "stay",
        "source_offer_id": "stay-123",
        "title": "Example Stay",
        "place_label": "London, United Kingdom",
        "availability_state": "available",
        "observed_at": datetime.now(UTC).isoformat(),
        "source_url": "https://www.booking.com/example",
        "currency": "GBP",
        "total_price": 250.0,
        "price_basis": "2 nights total",
    }
    payload.update(overrides)
    return payload


def test_provider_registry_is_lookup_only_and_has_no_oap_authority():
    validation = supply_integration.validate_supply_integration()
    providers = supply_integration.providers()

    assert validation["passed"] is True
    assert validation["persistent_partner_supply"] is False
    assert validation["creates_intelligence_worlds"] is False
    assert validation["creates_agents"] is False
    assert validation["creates_brain"] is False
    assert validation["external_provider_authority"] is False
    assert len(providers) == 1
    assert providers[0].provider_id == "booking_com"
    assert providers[0].provider_type == "optional_on_demand_external_lookup"
    assert providers[0].categories == ("stay", "attraction", "car_rental")
    assert providers[0].external_authority is False
    assert providers[0].supports_search is True
    assert providers[0].supports_booking_handoff is False
    assert providers[0].supports_direct_booking is False
    assert providers[0].supports_payment is False


def test_offer_requires_source_provenance_and_is_transient_reference_data():
    record = supply_integration.offer_record(_offer())

    assert record["provider_id"] == "booking_com"
    assert record["source_kind"] == "external_lookup_only"
    assert record["persistent_oap_supply"] is False
    assert record["observed_not_inferred"] is True
    assert record["provider_authority"] is False
    assert record["oap_authority"] is True
    assert record["booking_execution_authorized"] is False
    assert record["payment_execution_authorized"] is False

    with pytest.raises(ValueError, match="https_source_url_required"):
        supply_integration.normalize_offer(_offer(source_url="http://example.com"))

    with pytest.raises(ValueError, match="valid_observed_at_required"):
        supply_integration.normalize_offer(_offer(observed_at="not-a-time"))


def test_price_requires_currency_and_basis():
    with pytest.raises(ValueError, match="iso_currency_required_for_price"):
        supply_integration.normalize_offer(_offer(currency=None))

    with pytest.raises(ValueError, match="price_basis_required"):
        supply_integration.normalize_offer(_offer(price_basis=None))

    with pytest.raises(ValueError, match="total_price_cannot_be_negative"):
        supply_integration.normalize_offer(_offer(total_price=-1))


def test_unknown_provider_and_category_fail_closed():
    with pytest.raises(ValueError, match="unknown_supply_provider"):
        supply_integration.normalize_offer(_offer(provider_id="unknown"))

    with pytest.raises(ValueError, match="unsupported_supply_category"):
        supply_integration.normalize_offer(_offer(category="flight"))


def test_runtime_lookup_defaults_to_disconnected(monkeypatch):
    for suffix in (
        "CONNECTED",
        "SEARCH_CERTIFIED",
        "COMMERCIAL_TERMS_CERTIFIED",
        "BOOKING_CERTIFIED",
    ):
        monkeypatch.delenv(f"OAP_SUPPLY_BOOKING_COM_{suffix}", raising=False)

    current = supply_integration.status()
    provider = current["providers"][0]

    assert current["adapter_framework_ready"] is True
    assert current["provider_count"] == 1
    assert current["runtime_connected_count"] == 0
    assert current["live_search_provider_count"] == 0
    assert current["direct_booking_provider_count"] == 0
    assert current["live_supply_connected"] is False
    assert current["persistent_partner_supply"] is False
    assert current["booking_transactions_live"] is False
    assert current["payment_transactions_live"] is False
    assert current["commission_settlement_live"] is False
    assert provider["runtime_connected"] is False
    assert provider["live_search_certified"] is False
    assert provider["direct_booking_certified"] is False
    assert provider["persistent_import_allowed"] is False
    assert provider["partner_relationship"] is False
    assert current["external_provider_authority"] is False
    assert current["human_authority_final"] is True


def test_connected_lookup_does_not_become_live_oap_supply_booking_or_payment(monkeypatch):
    monkeypatch.setenv("OAP_SUPPLY_BOOKING_COM_CONNECTED", "1")
    monkeypatch.setenv("OAP_SUPPLY_BOOKING_COM_SEARCH_CERTIFIED", "1")
    monkeypatch.setenv("OAP_SUPPLY_BOOKING_COM_COMMERCIAL_TERMS_CERTIFIED", "1")
    monkeypatch.setenv("OAP_SUPPLY_BOOKING_COM_BOOKING_CERTIFIED", "1")

    current = supply_integration.status()
    provider = current["providers"][0]

    assert current["live_search_provider_count"] == 1
    assert current["live_supply_connected"] is False
    assert provider["live_search_certified"] is True
    assert provider["persistent_import_allowed"] is False
    assert provider["partner_relationship"] is False
    assert provider["booking_handoff_supported"] is False
    assert provider["direct_booking_certified"] is False
    assert current["booking_transactions_live"] is False
    assert current["payment_transactions_live"] is False
