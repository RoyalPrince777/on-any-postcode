from mission_control import humanitarian_map_intelligence


def test_humanitarian_map_status_binds_first_party_movement_intelligence():
    status = humanitarian_map_intelligence.humanitarian_map_intelligence_status()
    policy = status["first_party_policy"]

    assert status["mode"] == "civilian_emergency_map_production"
    assert status["demo_mode"] is False
    assert status["architecture_ready"] is True
    assert status["map_intelligence_bound"] is True
    assert status["canonical_spatial_binding"] == "EARTH_OUR_TURF_LOCAL_TO_GLOBAL"
    assert status["layer_count"] == 10
    assert status["civilian_only"] is True
    assert status["precise_civilian_location_public"] is False
    assert status["individual_tracking"] is False
    assert status["crowd_tracking"] is False
    assert status["military_overlays"] is False
    assert status["targeting"] is False
    assert status["surveillance"] is False
    assert status["autonomous_navigation"] is False
    assert status["human_authority_final"] is True
    assert policy["production_proprietary_map_api_allowed"] is False
    assert policy["production_proprietary_routing_api_allowed"] is False
    assert policy["oap_controlled_map_store_required"] is True
    assert policy["oap_controlled_route_engine_required"] is True
    assert policy["offline_navigation_target"] is True


def test_verified_civilian_map_view_can_be_prepared_without_navigation_claim():
    result = humanitarian_map_intelligence.prepare_humanitarian_map_view(
        area="Mitcham CR4",
        layers=("medical", "shelter", "connectivity", "hazards", "safe_route"),
        source_verified=True,
    )

    assert result["accepted"] is True
    assert result["reason"] == "prepared"
    assert result["map_architecture_ready"] is True
    assert result["navigation_claimed_safe"] is False
    assert result["route_recommendation_only"] is True
    assert result["precise_location_stored"] is False
    assert result["precise_civilian_location_public"] is False
    assert result["military_overlays"] is False
    assert result["targeting"] is False
    assert result["surveillance"] is False


def test_evidence_gated_map_layers_fail_closed_without_verified_source():
    result = humanitarian_map_intelligence.prepare_humanitarian_map_view(
        area="South London",
        layers=("hazards", "disruptions", "medical"),
        source_verified=False,
    )

    assert result["accepted"] is False
    assert result["reason"] == "verified_source_required"
    assert result["source_verified"] is False


def test_precise_civilian_location_cannot_be_prepared_for_public_share():
    result = humanitarian_map_intelligence.prepare_humanitarian_map_view(
        area="Greater London",
        layers=("administrative_boundaries",),
        source_verified=True,
        precise_location_requested=True,
        public_share=True,
    )

    assert result["accepted"] is False
    assert result["reason"] == "precise_civilian_location_publication_blocked"
    assert result["public_share"] is False
    assert result["precise_location_stored"] is False


def test_admin_boundary_view_does_not_require_live_hazard_evidence():
    result = humanitarian_map_intelligence.prepare_humanitarian_map_view(
        area="Ghana",
        layers=("administrative_boundaries",),
        source_verified=False,
    )

    assert result["accepted"] is True
    assert result["reason"] == "prepared"
