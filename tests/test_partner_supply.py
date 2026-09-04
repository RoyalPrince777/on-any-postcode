from datetime import UTC, datetime, timedelta

import pytest

from mission_control import partner_supply


def _payload() -> dict[str, object]:
    observed = datetime(2026, 9, 4, 14, 45, tzinfo=UTC)
    expires = observed + timedelta(hours=1)
    return {
        "provider_id": "booking_com",
        "search_key": "mitcham-london-2026-09-05-2026-09-07",
        "category": "stay",
        "source_scope": "Mitcham, London | 2026-09-05 to 2026-09-07 | 2 adults",
        "observed_at": observed.isoformat(),
        "expires_at": expires.isoformat(),
        "human_authority_approved": True,
        "offers": [
            {
                "source_offer_id": "17183351",
                "title": "Example partner stay",
                "place_label": "Mitcham, London",
                "availability_state": "available",
                "source_url": "https://www.booking.com/hotel/gb/example.html",
                "currency": "GBP",
                "total_price": 324,
                "price_basis": "searched stay total",
            }
        ],
    }


def test_partner_supply_migration_is_new_and_bounded():
    assert partner_supply.PARTNER_SUPPLY_MIGRATION_VERSION == "0008_partner_supply_snapshots"
    assert partner_supply.PARTNER_SUPPLY_TABLES == {
        "oap_partner_supply_snapshots",
        "oap_partner_supply_offers",
    }
    assert len(partner_supply.PARTNER_SUPPLY_MIGRATION_CHECKSUM) == 64
    assert partner_supply.MAX_SNAPSHOT_TTL == timedelta(hours=24)


def test_prepare_snapshot_requires_human_authority():
    payload = _payload()
    payload["human_authority_approved"] = False
    with pytest.raises(PermissionError, match="human_authority_approval_required"):
        partner_supply.prepare_snapshot(payload)


def test_prepare_snapshot_preserves_provider_provenance_and_price():
    result = partner_supply.prepare_snapshot(_payload())
    assert result["provider_id"] == "booking_com"
    assert result["category"] == "stay"
    assert len(result["source_digest"]) == 64
    assert len(result["offers"]) == 1
    offer = result["offers"][0]
    assert offer["source_offer_id"] == "17183351"
    assert offer["total_price_minor"] == 32400
    assert offer["currency"] == "GBP"
    assert offer["source_url"].startswith("https://www.booking.com/")


def test_prepare_snapshot_rejects_long_lived_stale_catalogue():
    payload = _payload()
    observed = datetime.fromisoformat(str(payload["observed_at"]))
    payload["expires_at"] = (observed + timedelta(hours=25)).isoformat()
    with pytest.raises(ValueError, match="partner_snapshot_ttl_must_be_within_24_hours"):
        partner_supply.prepare_snapshot(payload)


def test_prepare_snapshot_rejects_unknown_provider():
    payload = _payload()
    payload["provider_id"] = "not_a_provider"
    with pytest.raises(ValueError, match="unknown_supply_provider"):
        partner_supply.prepare_snapshot(payload)
