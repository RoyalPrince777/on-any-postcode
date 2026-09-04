from mission_control import international_humanitarian_intelligence


def test_international_humanitarian_is_single_canonical_civilian_umbrella():
    status = international_humanitarian_intelligence.international_humanitarian_intelligence_status()
    section_ids = tuple(item["id"] for item in status["sections"])

    assert status["name"] == "International Humanitarian Intelligence"
    assert status["mode"] == "civilian_humanitarian_production"
    assert status["demo_mode"] is False
    assert status["architecture_ready"] is True
    assert status["brain_count"] == 0
    assert status["intelligence_world_count_added"] == 0
    assert status["section_count"] == 10
    assert section_ids == (
        "world_crisis",
        "connectivity",
        "maps",
        "health",
        "aid_essentials",
        "family_reunification",
        "public_warning",
        "accessibility",
        "civilian_safety",
        "legal",
    )
    assert status["world_crisis_live_fetch_available"] is True
    assert status["human_authority_final"] is True
    assert status["independent_execute"] is False
    assert status["independent_approval"] is False


def test_all_humanitarian_children_keep_civilian_safety_boundaries():
    status = international_humanitarian_intelligence.international_humanitarian_intelligence_status()

    assert status["world_crisis"]["parent"] == "International Humanitarian Intelligence"
    assert status["world_crisis"]["civilian_only"] is True
    assert status["world_crisis"]["targeting"] is False
    assert status["world_crisis"]["surveillance"] is False
    assert status["connectivity"]["parent"] == "International Humanitarian Intelligence"
    assert status["connectivity"]["civilian_only"] is True
    assert status["maps"]["civilian_only"] is True
    assert status["health"]["diagnosis_authority"] is False
    assert status["aid_essentials"]["autonomous_dispatch"] is False
    assert status["family_reunification"]["precise_location_public"] is False
    assert status["public_warning"]["source_verification_required"] is True
    assert status["public_warning"]["autonomous_broadcast"] is False
    assert status["accessibility"]["architecture_ready"] is True
    assert status["civilian_safety"]["military_command"] is False
    assert status["civilian_safety"]["targeting"] is False
    assert status["civilian_safety"]["surveillance"] is False
    assert status["civilian_safety"]["weapon_support"] is False
    assert status["civilian_safety"]["offensive_cyber"] is False
    assert status["legal"]["parent"] == "International Humanitarian Intelligence"
    assert status["legal"]["legal_advice_claim"] is False
    assert status["legal"]["law_of_the_jungle"]["legal_authority"] is False


def test_physical_external_and_legal_readiness_claims_remain_evidence_gated():
    status = international_humanitarian_intelligence.international_humanitarian_intelligence_status()

    assert status["international_reach_claim"] is False
    assert status["live_humanitarian_data_feeds_claim"] is False
    assert status["live_jurisdiction_legal_feed_claim"] is False
    assert status["legal_advice_claim"] is False
    assert status["health"]["live_clinical_service_claim"] is False
    assert status["aid_essentials"]["live_global_supply_feed_claim"] is False
    assert status["accessibility"]["live_translation_claim"] is False
    assert status["legal"]["live_jurisdiction_database_ready"] is False
    assert status["legal"]["live_treaty_status_feed_ready"] is False
    assert status["legal"]["live_sanctions_feed_ready"] is False
    assert status["autonomous_dispatch"] is False
    assert status["autonomous_transmission"] is False
    assert status["network_execution_authority"] is False
