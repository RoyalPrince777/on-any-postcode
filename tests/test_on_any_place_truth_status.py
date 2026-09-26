from mission_control import (
    atlas_live_sources,
    local_map_intelligence,
    map_live_pattern,
    routing,
    routing_federation,
)


def _route_state():
    return {
        "runtime_verified": True,
        "oap_owned_endpoint": True,
        "road_vector_tiles": True,
        "geometry_exposed": True,
    }


def test_on_any_place_readiness_recognises_proven_navigation_without_unlocking_full_green(monkeypatch):
    monkeypatch.setattr(routing, "status", _route_state)
    monkeypatch.setattr(
        map_live_pattern,
        "status",
        lambda: {"authority_verified_feed": True},
    )
    monkeypatch.setattr(
        atlas_live_sources,
        "status",
        lambda: {"enabled": True},
    )
    monkeypatch.setattr(
        routing_federation,
        "status",
        lambda: {"connected_shard_count": 1},
    )

    state = local_map_intelligence.readiness_state()

    assert state["road_vector_tiles_proven"] is True
    assert state["route_geometry_proven"] is True
    assert state["turn_by_turn_software_ready"] is True
    assert state["voice_turn_guidance_ready"] is True
    assert state["off_route_reroute_ready"] is True
    assert state["live_disruption_authority_proven"] is True
    assert state["software_navigation_green"] is True
    assert state["wider_uk_routing_live"] is False
    assert state["overall_green"] is False
    assert "turn-by-turn navigation software proof" not in state["remaining_before_green"]
    assert "current authority-backed disruption feed proof" not in state["remaining_before_green"]
    assert "UK-wide owned routing shard coverage" in state["remaining_before_green"]


def test_on_any_place_readiness_fails_closed_when_runtime_proof_is_missing(monkeypatch):
    monkeypatch.setattr(
        routing,
        "status",
        lambda: {
            "runtime_verified": False,
            "oap_owned_endpoint": True,
            "road_vector_tiles": True,
            "geometry_exposed": True,
        },
    )
    monkeypatch.setattr(
        map_live_pattern,
        "status",
        lambda: {"authority_verified_feed": False},
    )
    monkeypatch.setattr(atlas_live_sources, "status", lambda: {"enabled": False})
    monkeypatch.setattr(
        routing_federation,
        "status",
        lambda: {"connected_shard_count": 1},
    )

    state = local_map_intelligence.readiness_state()

    assert state["road_vector_tiles_proven"] is False
    assert state["route_geometry_proven"] is False
    assert state["turn_by_turn_software_ready"] is False
    assert state["software_navigation_green"] is False
    assert state["overall_green"] is False


def test_public_status_exposes_truth_aligned_navigation_state(client, monkeypatch):
    monkeypatch.setattr(
        local_map_intelligence,
        "readiness_state",
        lambda: {
            "turn_by_turn_software_ready": True,
            "voice_turn_guidance_ready": True,
            "off_route_reroute_ready": True,
            "software_navigation_green": True,
            "live_disruption_authority_proven": True,
            "remaining_before_green": ("UK-wide owned routing shard coverage",),
        },
    )
    monkeypatch.setattr(routing, "status", lambda: {
        "provider_ownership": "oap_owned",
        "runtime_verified": True,
        "geometry_exposed": True,
        "road_vector_tiles": True,
        "road_vector_tile_min_zoom": 12,
    })
    monkeypatch.setattr(routing_federation, "status", lambda: {
        "ready_for_additional_owned_shards": True,
    })
    monkeypatch.setattr(atlas_live_sources, "status", lambda: {"enabled": True})
    monkeypatch.setattr(map_live_pattern, "status", lambda: {"authority_verified_feed": True})

    response = client.get("/map-intelligence/status")
    data = response.get_json()

    assert response.status_code == 200
    assert data["turn_by_turn"] is True
    assert data["voice_turn_guidance"] is True
    assert data["off_route_reroute"] is True
    assert data["software_navigation_green"] is True
    assert data["live_disruption_authority_proven"] is True
    assert "UK-wide owned routing shard coverage" in data["remaining_before_green"]
    assert data["payment_capture"] is False
    assert data["dispatch"] is False


def test_multiple_regional_shards_do_not_imply_uk_wide_proof(monkeypatch):
    from mission_control import (
        atlas_live_sources,
        certification,
        listing_media,
        map_live_pattern,
        maps_movement_direct_proof_runner,
        product_store,
        reviews,
        routing,
        routing_federation,
        travel_marketplace,
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
    monkeypatch.setattr(
        routing_federation,
        "status",
        lambda: {
            "connected_shard_count": 2,
            "uk_wide_owned_graph_proven": False,
        },
    )
    monkeypatch.setattr(listing_media, "status", lambda: {"schema_ready": True, "photo_count": 1})
    monkeypatch.setattr(
        travel_marketplace,
        "public_offers",
        lambda **kwargs: {"ready": True, "count": 1, "offers": [{"category": "event"}]},
    )
    monkeypatch.setattr(certification, "status", lambda: {"runtime_ready": True, "roles_ready": True})
    monkeypatch.setattr(product_store, "status", lambda: {"ready": True})
    monkeypatch.setattr(reviews, "status", lambda: {"ready": True})
    monkeypatch.setattr(
        maps_movement_direct_proof_runner,
        "route_matrix_status",
        lambda: {"certified": True},
    )

    state = local_map_intelligence.readiness_state()

    assert state["connected_routing_shards"] == 2
    assert state["wider_uk_routing_live"] is False
    assert "UK-wide owned routing shard coverage" in state["remaining_before_green"]
