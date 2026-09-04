"""Runtime projection for the approved OAP Earth Intelligence world.

Earth Intelligence powers the EARTH OUR TURF place experience.  It remains one
of the seven governed Intelligence worlds, not another OAP brain or agent
family.  Weather is the first live environmental input; wider Earth domains
remain fail-closed until real sources exist.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

COMPONENTS = (
    "weather_climate",
    "atmosphere",
    "land",
    "water",
    "ecosystems",
    "agriculture",
    "resources",
    "disaster_awareness",
    "sustainability",
    "planetary_wellbeing",
)

# Local is an umbrella, not a single administrative type. Borough/District is
# deliberately kept inside the Local family while every country can map its
# real administrative names onto these OAP concepts.
LOCAL_DETAIL_LEVELS: tuple[str, ...] = (
    "spot",
    "street_block",
    "estate_village_neighbourhood",
    "ward_local_area",
    "postcode_or_equivalent",
    "borough_district_or_equivalent",
)
EARTH_OUR_TURF_LEVELS: tuple[str, ...] = (
    "local",
    "region_county_or_equivalent",
    "country",
    "continent",
    "global",
)

EARTH_OUR_TURF_COMPOSITION: tuple[dict[str, str], ...] = (
    {"source": "Earth Intelligence", "role": "place, land, climate, nature and environmental context"},
    {"source": "Civic Intelligence", "role": "community and public-service context"},
    {"source": "Civilisation Intelligence", "role": "history, culture and institutions"},
    {"source": "Language Intelligence", "role": "languages, variants and communication context"},
    {"source": "Life Intelligence", "role": "practical education, skills and real-life context"},
    {"source": "Movement Intelligence", "role": "routes, transport and movement between places"},
    {"source": "Signal", "role": "current trusted updates"},
    {"source": "Chronicle", "role": "place memory and stories"},
    {"source": "Community Power", "role": "participation, leadership, education and Nature growth"},
)

NATURE_GROWTH_MODEL: tuple[dict[str, str], ...] = (
    {"id": "seed", "emoji": "🌱", "meaning": "How an OAP story or connection begins."},
    {"id": "branches", "emoji": "🌿", "meaning": "How connections spread."},
    {"id": "leaves", "emoji": "🍃", "meaning": "Active people, creators, businesses, communities and opportunities."},
    {"id": "bloom", "emoji": "🌺", "meaning": "Something new launches or comes alive."},
    {"id": "harvest", "emoji": "🥭", "meaning": "Real outcomes or value are created."},
    {"id": "journey", "emoji": "🕰️", "meaning": "How the growth develops over time."},
    {"id": "canopy", "emoji": "🌳", "meaning": "Overall Local-to-Global reach."},
)


def _text(value: object) -> str:
    return str(value or "").strip()


def _place_model() -> dict[str, Any]:
    return {
        "experience": "EARTH OUR TURF",
        "tagline": "Born Local. Built Global. Earth Is Our Turf.",
        "canonical_spatial_binding": "EARTH_OUR_TURF_LOCAL_TO_GLOBAL",
        "local_detail_levels": LOCAL_DETAIL_LEVELS,
        "earth_levels": EARTH_OUR_TURF_LEVELS,
        "borough_is_local": True,
        "country_specific_admin_mapping_required": True,
        "composition": EARTH_OUR_TURF_COMPOSITION,
        "community_power": {
            "owns_leadership_and_education": True,
            "owns_nature_growth_model": True,
            "nature_growth_model": NATURE_GROWTH_MODEL,
        },
        "world_rooms_role": "community_interaction_feature_inside_places",
    }


def from_weather(weather: Mapping[str, Any]) -> dict[str, Any]:
    """Project verified Weather Intelligence into bounded Earth context."""

    weather_signal = weather.get("intelligence")
    weather_ready = isinstance(weather_signal, Mapping)
    return {
        "name": "Earth Intelligence",
        "world_id": "earth",
        "architecture_passed": True,
        "component_count": len(COMPONENTS),
        "components": COMPONENTS,
        "nature_organ": "OAP Nature",
        "weather_intelligence_connected": weather_ready,
        # Compatibility field retained for existing clients; canonical binding is
        # exposed separately and new code must use the Local-to-Global model.
        "spatial_binding": "THE_SPOT_POSTCODE_TO_UNIVERSE",
        "canonical_spatial_binding": "EARTH_OUR_TURF_LOCAL_TO_GLOBAL",
        "place_model": _place_model(),
        "current_environment": {
            "condition": _text(weather_signal.get("condition")) if weather_ready else "",
            "advisory_level": _text(weather_signal.get("advisory_level")) if weather_ready else "unavailable",
            "rain_signal": _text(weather_signal.get("rain_signal")) if weather_ready else "unavailable",
            "wind_signal": _text(weather_signal.get("wind_signal")) if weather_ready else "unavailable",
            "thermal_signal": _text(weather_signal.get("thermal_signal")) if weather_ready else "unavailable",
            "observation_time": _text(weather_signal.get("observation_time")) if weather_ready else "",
        },
        "coverage": {
            "weather": "live_bootstrap" if weather_ready else "unavailable",
            "atmosphere": "weather_signals_only" if weather_ready else "unavailable",
            "land": "spatial_context_only",
            "water": "not_connected",
            "ecosystems": "not_connected",
            "agriculture": "not_connected",
            "resources": "not_connected",
            "disaster_awareness": "weather_advisory_only" if weather_ready else "not_connected",
            "sustainability": "architecture_only",
            "planetary_wellbeing": "architecture_only",
        },
        "live_environment_ready": weather_ready,
        "full_earth_runtime_ready": False,
        "human_authority_final": True,
        "can_execute": False,
        "truth_boundary": (
            "Earth Intelligence currently uses verified place context and Weather Intelligence only. "
            "EARTH OUR TURF composition is defined, but water, ecosystem, agriculture, resource, "
            "wider disaster and broader place-knowledge feeds remain unconnected and are never inferred."
        ),
    }


def status(*, weather_ready: bool) -> dict[str, Any]:
    """Return architecture/readiness without making network calls."""

    return {
        "name": "Earth Intelligence",
        "world_id": "earth",
        "architecture_passed": True,
        "component_count": len(COMPONENTS),
        "components": COMPONENTS,
        "nature_organ_connected": True,
        "weather_intelligence_connected": bool(weather_ready),
        "the_spot_connected": True,
        "spatial_binding": "POSTCODE_TO_UNIVERSE",
        "canonical_spatial_binding": "EARTH_OUR_TURF_LOCAL_TO_GLOBAL",
        "place_model": _place_model(),
        "full_earth_runtime_ready": False,
        "human_authority_final": True,
        "can_execute": False,
        "truth_boundary": (
            "The Earth Intelligence world, EARTH OUR TURF place model and OAP Nature organ are present. "
            "Weather is the first live sensing connection; broader Earth and place observations remain gated."
        ),
    }
