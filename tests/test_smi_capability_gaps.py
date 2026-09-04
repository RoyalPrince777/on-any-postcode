from __future__ import annotations

from mission_control import (
    earth_intelligence,
    international_humanitarian_intelligence,
    language_intelligence,
    life_intelligence,
    movement_intelligence,
    smi_capabilities,
    technology_intelligence,
)


def test_earth_intelligence_uses_canonical_local_to_global_spatial_model():
    status = earth_intelligence.status(weather_ready=False)
    assert status["architecture_passed"] is True
    assert status["brain_count"] == 0
    assert status["intelligence_world_count_added"] == 0
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


def test_language_intelligence_is_bounded_and_uses_one_oap_language_layer():
    status = language_intelligence.language_intelligence_status()
    assert status["architecture_passed"] is True
    assert status["brain_count"] == 0
    assert status["intelligence_world_count_added"] == 0
    assert status["independent_execution"] is False
    assert status["human_authority_final"] is True


def test_life_intelligence_is_bounded_and_community_power_based():
    status = life_intelligence.life_intelligence_status()
    assert status["architecture_passed"] is True
    assert status["brain_count"] == 0
    assert status["intelligence_world_count_added"] == 0
    assert status["independent_execution"] is False
    assert status["human_authority_final"] is True


def test_movement_intelligence_remains_non_executing():
    status = movement_intelligence.movement_intelligence_status()
    assert status["architecture_passed"] is True
    assert status["brain_count"] == 0
    assert status["intelligence_world_count_added"] == 0
    assert status["independent_execution"] is False
    assert status["human_authority_final"] is True


def test_technology_intelligence_keeps_6g_evidence_gated():
    status = technology_intelligence.technology_intelligence_status()
    assert status["architecture_passed"] is True
    assert status["brain_count"] == 0
    assert status["intelligence_world_count_added"] == 0
    assert status["6g_architecture_ready"] is True
    assert status["6g_production_network_ready"] is False
    assert status["independent_execution"] is False
    assert status["human_authority_final"] is True


def test_international_humanitarian_intelligence_is_civilian_only():
    status = international_humanitarian_intelligence.international_humanitarian_intelligence_status()
    assert status["architecture_passed"] is True
    assert status["brain_count"] == 0
    assert status["intelligence_world_count_added"] == 0
    assert status["civilian_only"] is True
    assert status["targeting"] is False
    assert status["surveillance"] is False
    assert status["independent_execution"] is False
    assert status["human_authority_final"] is True


def test_specialist_capabilities_do_not_mutate_locked_seven_worlds():
    validation = smi_capabilities.validate_smi_capabilities()
    status = smi_capabilities.smi_capability_status()
    assert validation["passed"] is True
    assert validation["checks"]["intelligence_worlds"] == 7
    assert validation["checks"]["cross_system_capabilities"] == 3
    assert tuple(
        item["id"] for item in status["cross_system_capabilities"]
    ) == ("technology", "international_humanitarian", "multimodal")
    assert validation["checks"]["brain_count_added_by_agi"] == 0
    assert status["specialist_status"]["technology"]["6g_architecture_ready"] is True
    humanitarian = status["specialist_status"]["international_humanitarian"]
    assert humanitarian["architecture_passed"] is True
    assert humanitarian["legal"]["architecture_ready"] is True
    assert humanitarian["legal"]["law_of_the_jungle"]["legal_authority"] is False
    assert status["agi_core"]["agi_achieved"] is False
    assert status["independent_execution"] is False
    assert status["human_authority_final"] is True
