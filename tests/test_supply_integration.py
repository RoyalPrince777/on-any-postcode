from datetime import UTC, datetime

import pytest

from oap.smi import supply_integration


def _observation(**overrides):
    payload = {
        "source_name": "External Travel Source",
        "category": "stay",
        "title": "Example Stay",
        "place_label": "London, United Kingdom",
        "observed_at": datetime.now(UTC).isoformat(),
        "source_url": "https://example.com/stay/123",
    }
    payload.update(overrides)
    return payload


def test_external_provider_registry_is_intentionally_empty():
    validation = supply_integration.validate_supply_integration()

    assert validation["passed"] is True
    assert supply_integration.providers() == ()
    assert validation["provider_count"] == 0
    assert validation["external_data_fetch_allowed"] is True
    assert validation["external_catalogue_ingest_allowed"] is False
    assert validation["external_provider_authority"] is False
    assert validation["creates_intelligence_worlds"] is False
    assert validation["creates_agents"] is False
    assert validation["creates_brain"] is False


def test_external_observation_keeps_research_boundary():
    record = supply_integration.external_observation_record(_observation())

    assert record["source_name"] == "External Travel Source"
    assert record["research_only"] is True
    assert record["catalogue_ingest_authorized"] is False
    assert record["booking_execution_authorized"] is False
    assert record["payment_execution_authorized"] is False
    assert record["external_provider_authority"] is False
    assert record["human_authority_final"] is True


def test_external_observation_requires_https_and_observation_time():
    with pytest.raises(ValueError, match="https_source_url_required"):
        supply_integration.normalize_external_observation(
            _observation(source_url="http://example.com")
        )

    with pytest.raises(ValueError, match="valid_observed_at_required"):
        supply_integration.normalize_external_observation(
            _observation(observed_at="not-a-time")
        )

    with pytest.raises(ValueError, match="unsupported_supply_category"):
        supply_integration.normalize_external_observation(
            _observation(category="flight")
        )


def test_unregistered_marketplace_offer_cannot_enter_catalogue():
    with pytest.raises(ValueError, match="unknown_supply_provider"):
        supply_integration.normalize_offer(
            {
                "provider_id": "booking_com",
                "category": "stay",
                "source_offer_id": "stay-123",
                "title": "Example Stay",
                "place_label": "London",
                "availability_state": "available",
                "observed_at": datetime.now(UTC).isoformat(),
                "source_url": "https://example.com/stay/123",
            }
        )


def test_runtime_status_has_no_external_commercial_provider():
    current = supply_integration.status()

    assert current["adapter_framework_ready"] is True
    assert current["provider_count"] == 0
    assert current["runtime_connected_count"] == 0
    assert current["live_search_provider_count"] == 0
    assert current["direct_booking_provider_count"] == 0
    assert current["live_supply_connected"] is False
    assert current["booking_transactions_live"] is False
    assert current["payment_transactions_live"] is False
    assert current["commission_settlement_live"] is False
    assert current["external_data_fetch_allowed"] is True
    assert current["external_catalogue_ingest_allowed"] is False
    assert current["external_provider_authority"] is False
    assert current["human_authority_final"] is True
