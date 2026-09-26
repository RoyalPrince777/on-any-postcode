from mission_control import (
    atlas_live_sources,
    listing_media,
    local_map_intelligence,
    map_live_pattern,
    routing,
    routing_federation,
    travel_marketplace,
)


def test_place_lookup_records_opening_hours_source_evidence(monkeypatch):
    monkeypatch.setenv("OAP_ATLAS_OPEN_DATA_ENABLED", "true")
    monkeypatch.setattr(
        atlas_live_sources.urllib.request,
        "urlopen",
        lambda request, timeout: type(
            "Response",
            (),
            {
                "__enter__": lambda self: self,
                "__exit__": lambda self, *args: False,
                "read": lambda self, n: b'''[
                    {
                      "place_id": 1,
                      "lat": "51.4",
                      "lon": "-0.16",
                      "display_name": "Example Cafe, Mitcham",
                      "class": "amenity",
                      "type": "cafe",
                      "extratags": {
                        "opening_hours": "Mo-Su 08:00-20:00",
                        "website": "https://example.test"
                      }
                    }
                ]''',
            },
        )(),
    )

    result = atlas_live_sources.fetch_places("Mitcham")

    assert result["result_count"] == 1
    assert result["results"][0]["opening_hours"] == "Mo-Su 08:00-20:00"
    assert result["results"][0]["opening_hours_source_backed"] is True
    assert result["results"][0]["website_source_backed"] is True
    evidence = atlas_live_sources.last_fetch_status()
    assert evidence["opening_hours_count"] == 1
    assert evidence["website_count"] == 1


def test_readiness_uses_real_event_inventory_and_listing_photo_proof(monkeypatch):
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
    monkeypatch.setattr(
        map_live_pattern,
        "status",
        lambda: {"authority_verified_feed": True},
    )
    monkeypatch.setattr(
        atlas_live_sources,
        "status",
        lambda: {
            "enabled": True,
            "last_fetch": {
                "opening_hours_count": 2,
                "freshness": "fresh",
            },
        },
    )
    monkeypatch.setattr(
        routing_federation,
        "status",
        lambda: {"connected_shard_count": 1},
    )
    monkeypatch.setattr(
        listing_media,
        "status",
        lambda: {"schema_ready": True, "photo_count": 3},
    )
    monkeypatch.setattr(
        travel_marketplace,
        "public_offers",
        lambda **kwargs: {
            "ready": True,
            "count": 1,
            "offers": [{"category": "event", "observed_at": "2026-09-26T13:00:00+00:00"}],
        },
    )

    state = local_map_intelligence.readiness_state()

    assert state["opening_hours_source_proven"] is True
    assert state["event_inventory_source_proven"] is True
    assert state["first_party_listing_photo_proven"] is True
    assert "source-backed event inventory proof" not in state["remaining_before_green"]
    assert "opening-hours source proof" not in state["remaining_before_green"]
    assert "first-party listing photo proof" not in state["remaining_before_green"]
    assert "first-party reviews proof" in state["remaining_before_green"]
    assert state["overall_green"] is False


def test_source_proof_fails_closed_when_evidence_is_absent(monkeypatch):
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
        lambda: {"enabled": True, "last_fetch": {"opening_hours_count": 0, "freshness": "fresh"}},
    )
    monkeypatch.setattr(routing_federation, "status", lambda: {"connected_shard_count": 1})
    monkeypatch.setattr(listing_media, "status", lambda: {"schema_ready": True, "photo_count": 0})
    monkeypatch.setattr(
        travel_marketplace,
        "public_offers",
        lambda **kwargs: {"ready": True, "count": 0, "offers": []},
    )

    state = local_map_intelligence.readiness_state()

    assert state["opening_hours_source_proven"] is False
    assert state["event_inventory_source_proven"] is False
    assert state["first_party_listing_photo_proven"] is False
    assert "source-backed event inventory proof" in state["remaining_before_green"]
    assert "opening-hours source proof" in state["remaining_before_green"]
    assert "first-party listing photo proof" in state["remaining_before_green"]
