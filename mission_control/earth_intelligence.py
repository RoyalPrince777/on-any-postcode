"""OAP Earth Intelligence.

Earth Intelligence composes verified spatial context and existing Weather
Intelligence into one planet-context view for OAP World and The Spot. It does
not fetch providers itself and does not claim environmental or hazard feeds
that are not yet connected.
"""

from __future__ import annotations

from typing import Any, Mapping

COMPONENTS = (
    "spatial_context",
    "weather_context",
    "environment_context",
    "terrain_context",
    "hazard_context",
    "nature_context",
    "local_conditions",
    "earth_memory_boundary",
)


def compose(location: Mapping[str, Any], weather: Mapping[str, Any]) -> dict[str, Any]:
    weather_intelligence = weather.get("intelligence")
    weather_ready = isinstance(weather_intelligence, Mapping)
    return {
        "name": "OAP Earth Intelligence",
        "scope": "Earth",
        "spatial_context": {
            "postcode": str(location.get("postcode") or ""),
            "borough": str(location.get("borough") or ""),
            "county": str(location.get("county") or ""),
            "country": str(location.get("country") or ""),
            "continent": str(location.get("continent") or ""),
            "global": str(location.get("global") or "Global"),
            "universe": str(location.get("universe") or "Universe"),
        },
        "local_conditions": {
            "temperature": weather.get("temperature"),
            "feels_like": weather.get("feels_like"),
            "precipitation": weather.get("precipitation"),
            "wind_speed": weather.get("wind_speed"),
            "condition": weather_intelligence.get("condition") if weather_ready else "Conditions unavailable",
            "advisory_level": weather_intelligence.get("advisory_level") if weather_ready else "unavailable",
            "observation_time": str(weather.get("time") or ""),
        },
        "weather_intelligence_connected": weather_ready,
        "environment_intelligence_ready": False,
        "terrain_intelligence_ready": False,
        "hazard_intelligence_ready": False,
        "nature_intelligence_ready": False,
        "earth_memory_connected": False,
        "the_spot_connected": True,
        "spatial_binding": "POSTCODE_TO_UNIVERSE",
        "truth_boundary": (
            "Earth Intelligence currently composes verified spatial and weather context only; "
            "environment, terrain, hazards, nature observations and Earth memory remain gated "
            "until verified OAP-controlled data paths are connected."
        ),
    }


def status(*, weather_ready: bool) -> dict[str, Any]:
    return {
        "name": "OAP Earth Intelligence",
        "architecture_passed": True,
        "component_count": len(COMPONENTS),
        "components": COMPONENTS,
        "weather_intelligence_connected": bool(weather_ready),
        "the_spot_connected": True,
        "spatial_binding": "POSTCODE_TO_UNIVERSE",
        "environment_intelligence_ready": False,
        "terrain_intelligence_ready": False,
        "hazard_intelligence_ready": False,
        "nature_intelligence_ready": False,
        "earth_memory_connected": False,
        "ready": bool(weather_ready),
        "fully_operational": False,
        "truth_boundary": (
            "Earth Intelligence is live as a spatial-weather composition layer; broader Earth "
            "observation capabilities remain fail-closed until verified sources are connected."
        ),
    }
