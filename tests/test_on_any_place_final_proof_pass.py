from datetime import datetime
from zoneinfo import ZoneInfo

from mission_control import (
    atlas_live_sources,
    certification,
    hrm_durable_receipt,
    listing_media,
    local_map_intelligence,
    map_live_pattern,
    maps_movement_direct_proof_runner,
    product_store,
    routing,
    routing_federation,
    travel_marketplace,
)


def test_open_now_evaluator_proves_supported_uk_hours_and_fails_closed_elsewhere():
    london = ZoneInfo("Europe/London")
    monday_noon = datetime(2026, 9, 28, 12, 0, tzinfo=london)

    open_state = atlas_live_sources.evaluate_open_now(
        "Mo-Fr 09:00-17:00", country_code="gb", now=monday_noon
    )
    assert open_state["state"] == "open"
    assert open_state["proven"] is True

    unknown_timezone = atlas_live_sources.evaluate_open_now(
        "Mo-Fr 09:00-17:00", country_code="gh", now=monday_noon
    )
    assert unknown_timezone["state"] == "unknown"
    assert unknown_timezone["proven"] is False

    unsupported = atlas_live_sources.evaluate_open_now(
        "sunrise-sunset", country_code="gb", now=monday_noon
    )
    assert unsupported["state"] == "unknown"
    assert unsupported["proven"] is False


def test_route_matrix_status_uses_durable_read_back_receipt(monkeypatch):
    monkeypatch.setattr(
        hrm_durable_receipt,
        "latest_receipt_status",
        lambda signal_id: {
            "found": True,
            "receipt_id": "receipt-1",
            "read_back_verified": True,
            "capture_passed": True,
            "public_probe_pass": True,
            "private_fail_closed_pass": True,
            "authority_transferred": False,
            "recorded_at": "2026-09-26T16:00:00+00:00",
        },
    )

    state = maps_movement_direct_proof_runner.route_matrix_status()
    assert state["certified"] is True
    assert state["signal"] == "green"
    assert state["live_capture_present"] is True
    assert state["receipt_read_back_verified"] is True


def test_on_any_place_reuses_existing_market_and_war_room_proof(monkeypatch):
    monkeypatch.setattr(product_store, "status", lambda: {"ready": True})
    monkeypatch.setattr(
        certification,
        "status",
        lambda: {"runtime_ready": True, "roles_ready": True},
    )
    monkeypatch.setattr(
        maps_movement_direct_proof_runner,
        "route_matrix_status",
        lambda: {"certified": True},
    )

    monkeypatch.setattr(
        routing,
        "status",
        lambda: {
            "runtime_verified": True,
            "oap_owned_endpoint": True,
            "road_vector_tiles": True,
            "geometry_exposed": True,
        },
    )
    monkeypatch.setattr(map_live_pattern, "status", lambda: {"authority_verified_feed": True})
    monkeypatch.setattr(
        atlas_live_sources,
        "status",
        lambda: {"enabled": True, "last_fetch": {"opening_hours_count": 1, "freshness": "fresh"}},
    )
    monkeypatch.setattr(routing_federation, "status", lambda: {"connected_shard_count": 1})
    monkeypatch.setattr(listing_media, "status", lambda: {"schema_ready": True, "photo_count": 1})
    monkeypatch.setattr(
        travel_marketplace,
        "public_offers",
        lambda **kwargs: {"ready": True, "count": 1, "offers": [{"category": "event"}]},
    )

    state = local_map_intelligence.readiness_state()
    assert state["business_owner_listing_tools_ready"] is True
    assert state["war_room_proof_runner_pass"] is True
    assert state["open_now_evaluator_ready"] is True
    assert "business owner listing tools" not in state["remaining_before_green"]
    assert "combined War Room proof-runner pass" not in state["remaining_before_green"]
    assert "first-party reviews proof" in state["remaining_before_green"]
    assert "UK-wide owned routing shard coverage" in state["remaining_before_green"]
