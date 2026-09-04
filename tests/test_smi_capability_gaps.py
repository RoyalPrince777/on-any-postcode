from mission_control import (
    earth_intelligence,
    language_intelligence,
    life_intelligence,
    smi_capabilities,
)
from oap.smi.agi_core import AGICore


def test_agi_core_is_inside_smi_without_claiming_achieved_agi():
    status = AGICore().status()
    assert status["ready"] is True
    assert status["kind"] == "capability_layer"
    assert status["brain_count"] == 0
    assert status["agi_achieved"] is False
    assert status["general_intelligence_certified"] is False
    assert status["independent_execute"] is False
    assert status["independent_approval"] is False
    assert status["human_authority_final"] is True


def test_agi_core_routes_cross_domain_requests_to_specialists():
    route = AGICore().route(
        "How do I travel from Mitcham to Ghana, learn Twi and find a trade?",
        "GENERAL",
    )
    domains = set(route["domain_ids"])
    assert {"earth", "movement", "language", "life", "akan"} <= domains
    assert route["cross_domain"] is True
    assert route["synthesis_required"] is True
    assert route["decision_authority"] is False
    assert route["execution_authority"] is False


def test_language_intelligence_reuses_validated_language_hub():
    status = language_intelligence.language_intelligence_status()
    assert status["architecture_passed"] is True
    assert status["oap_world_language_hub_connected"] is True
    assert status["live_translation_ready"] is False
    assert status["speech_learning_ready"] is False
    assert status["youth_safeguarding_required"] is True
    assert status["can_execute"] is False


def test_life_intelligence_separates_adult_youth_and_covers_trade_families():
    status = life_intelligence.life_intelligence_status()
    section_ids = {item["id"] for item in status["sections"]}
    trade_ids = {item["id"] for item in status["trade_families"]}
    assert status["architecture_passed"] is True
    assert {"adult", "youth", "trades", "professions", "money", "business"} <= section_ids
    assert {"construction", "electrical", "automotive", "digital", "green", "marine_air"} <= trade_ids
    assert status["governance"]["adult_youth_separated"] is True
    assert status["governance"]["oap_course_equals_professional_licence"] is False
    assert status["credential_runtime_ready"] is False
    assert status["can_execute"] is False


def test_earth_our_turf_local_to_global_is_canonical_while_legacy_binding_remains_compatible():
    status = earth_intelligence.status(weather_ready=False)
    place = status["place_model"]
    assert status["canonical_spatial_binding"] == "EARTH_OUR_TURF_LOCAL_TO_GLOBAL"
    assert status["spatial_binding"] == "POSTCODE_TO_UNIVERSE"
    assert place["experience"] == "EARTH OUR TURF"
    assert place["borough_is_local"] is True
    assert place["earth_levels"] == (
        "local",
        "region_county_or_equivalent",
        "country",
        "continent",
        "global",
    )
    growth = place["community_power"]["nature_growth_model"]
    assert tuple(item["id"] for item in growth) == (
        "seed", "branches", "leaves", "bloom", "harvest", "journey", "canopy"
    )


def test_specialist_capabilities_do_not_mutate_locked_seven_worlds():
    validation = smi_capabilities.validate_smi_capabilities()
    status = smi_capabilities.smi_capability_status()
    assert validation["passed"] is True
    assert validation["checks"]["intelligence_worlds"] == 7
    assert validation["checks"]["cross_system_capabilities"] == 4
    assert validation["checks"]["brain_count_added_by_agi"] == 0
    assert status["agi_core"]["agi_achieved"] is False
    assert status["independent_execution"] is False
    assert status["human_authority_final"] is True
