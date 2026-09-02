"""Runtime projection for the already-approved OAP Earth Intelligence world.

Earth Intelligence is a governed Intelligence world, not an eighth agent family
and not another OAP World/navigation hierarchy. This module combines verified
place/weather evidence into a bounded environmental context while keeping
unconnected Earth domains explicitly unavailable.
"""

from __future__ import annotations

from typing import Any, Mapping

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


def _text(value: object) -> str:
    return str(value or "").strip()


def from_weather(
    weather: Mapping[str, Any],
    *,
    postcode: object = "",
    borough: object = "",
    county: object = "",
    country: object = "",
    continent: object = "",
) -> dict[str, Any]:
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
        "spatial_binding": {
            "postcode": _text(postcode),
            "borough": _text(borough),
            "county": _text(county),
            "country": _text(country),
            "continent": _text(continent),
        },
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
            "Earth Intelligence is connected to verified place and Weather Intelligence evidence. "
            "Water, ecosystem, agriculture, resource and wider disaster feeds remain unconnected "
            "and are never inferred from weather alone."
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
        "full_earth_runtime_ready": False,
        "human_authority_final": True,
        "can_execute": False,
        "truth_boundary": (
            "The approved Earth Intelligence world and OAP Nature organ are present. "
            "Weather is the first live sensing connection; broader Earth observations remain gated."
        ),
    }
