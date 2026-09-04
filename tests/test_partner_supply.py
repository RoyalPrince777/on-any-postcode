from datetime import UTC, datetime, timedelta

import pytest

from mission_control import partner_supply


def _payload() -> dict[str, object]:
    observed = datetime(2026, 9, 4, 14, 45, tzinfo=UTC)
    return {
        "provider_id": "booking_com",
        "search_key": "external-research-example",
        "category": "stay",
        "source_scope": "research only",
        "observed_at": observed.isoformat(),
        "expires_at": (observed + timedelta(hours=1)).isoformat(),
        "human_authority_approved": True,
        "offers": [
            {
                "source_offer_id": "external-1",
                "title": "External research observation",
                "place_label": "London",
                "availability_state": "available",
                "source_url": "https://example.com/stay/1",
                "currency": "GBP",
                "total_price": 100,
                "price_basis": "research observation",
            }
        ],
    }


def test_historical_partner_schema_remains_checksum_visible_for_audit():
    assert partner_supply.PARTNER_SUPPLY_MIGRATION_VERSION == "0008_partner_supply_snapshots"
    assert partner_supply.PARTNER_SUPPLY_TABLES == {
        "oap_partner_supply_snapshots",
        "oap_partner_supply_offers",
    }
    assert len(partner_supply.PARTNER_SUPPLY_MIGRATION_CHECKSUM) == 64


def test_partner_import_path_is_effectively_retired_by_empty_provider_registry():
    with pytest.raises(ValueError, match="unknown_supply_provider"):
        partner_supply.prepare_snapshot(_payload())


def test_historical_import_still_requires_human_authority_before_validation():
    payload = _payload()
    payload["human_authority_approved"] = False
    with pytest.raises(PermissionError, match="human_authority_approval_required"):
        partner_supply.prepare_snapshot(payload)
