"""OAP Weather Intelligence.

This module interprets bounded live weather observations already retrieved by
``location_intelligence``. It does not fetch network data itself and it never
fabricates an observation when the upstream live source is unavailable.
"""

from __future__ import annotations

from typing import Any, Mapping

COMPONENTS = (
    "observation",
    "forecast",
    "precipitation",
    "wind",
    "thermal",
    "local_advisory",
    "spatial_binding",
)

_WMO_CONDITIONS = {
    0: ("Clear", "☀️"),
    1: ("Mainly clear", "🌤️"),
    2: ("Partly cloudy", "⛅"),
    3: ("Overcast", "☁️"),
    45: ("Fog", "🌫️"),
    48: ("Freezing fog", "🌫️"),
    51: ("Light drizzle", "🌦️"),
    53: ("Drizzle", "🌦️"),
    55: ("Heavy drizzle", "🌧️"),
    56: ("Freezing drizzle", "🌧️"),
    57: ("Heavy freezing drizzle", "🌧️"),
    61: ("Light rain", "🌦️"),
    63: ("Rain", "🌧️"),
    65: ("Heavy rain", "🌧️"),
    66: ("Freezing rain", "🌧️"),
    67: ("Heavy freezing rain", "🌧️"),
    71: ("Light snow", "🌨️"),
    73: ("Snow", "❄️"),
    75: ("Heavy snow", "❄️"),
    77: ("Snow grains", "🌨️"),
    80: ("Light rain showers", "🌦️"),
    81: ("Rain showers", "🌧️"),
    82: ("Heavy rain showers", "🌧️"),
    85: ("Snow showers", "🌨️"),
    86: ("Heavy snow showers", "❄️"),
    95: ("Thunderstorm", "⛈️"),
    96: ("Thunderstorm with hail", "⛈️"),
    99: ("Severe thunderstorm with hail", "⛈️"),
}


def _number(value: object) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _maximum_rain_chance(days: object) -> float | None:
    if not isinstance(days, list):
        return None
    values: list[float] = []
    for day in days:
        if isinstance(day, Mapping):
            value = _number(day.get("rain_chance"))
            if value is not None:
                values.append(value)
    return max(values) if values else None


def _advisory_level(*, code: int | None, precipitation: float | None, wind: float | None, temperature: float | None, rain_chance: float | None) -> str:
    if code in {95, 96, 99}:
        return "red"
    if code in {65, 67, 75, 82, 86}:
        return "amber"
    if wind is not None and wind >= 60:
        return "amber"
    if precipitation is not None and precipitation >= 8:
        return "amber"
    if temperature is not None and (temperature <= -5 or temperature >= 35):
        return "amber"
    if rain_chance is not None and rain_chance >= 70:
        return "yellow"
    if code in {45, 48, 51, 53, 55, 56, 57, 61, 63, 66, 71, 73, 77, 80, 81, 85}:
        return "yellow"
    return "green"


def enrich(observation: Mapping[str, Any]) -> dict[str, Any]:
    """Add deterministic Weather Intelligence signals to a live observation."""

    result = dict(observation)
    raw_code = observation.get("weather_code")
    try:
        code = int(raw_code) if raw_code is not None else None
    except (TypeError, ValueError):
        code = None
    condition, icon = _WMO_CONDITIONS.get(code, ("Conditions unavailable", "🌦️"))
    precipitation = _number(observation.get("precipitation"))
    wind = _number(observation.get("wind_speed"))
    temperature = _number(observation.get("temperature"))
    rain_chance = _maximum_rain_chance(observation.get("days"))

    result["intelligence"] = {
        "name": "OAP Weather Intelligence",
        "condition": condition,
        "icon": icon,
        "advisory_level": _advisory_level(
            code=code,
            precipitation=precipitation,
            wind=wind,
            temperature=temperature,
            rain_chance=rain_chance,
        ),
        "rain_signal": (
            "high" if rain_chance is not None and rain_chance >= 70
            else "possible" if rain_chance is not None and rain_chance >= 35
            else "low"
        ),
        "wind_signal": (
            "strong" if wind is not None and wind >= 40
            else "moderate" if wind is not None and wind >= 20
            else "light"
        ),
        "thermal_signal": (
            "hot" if temperature is not None and temperature >= 30
            else "cold" if temperature is not None and temperature <= 5
            else "mild"
        ),
        "observation_time": str(observation.get("time") or ""),
        "spatial_binding": "THE_SPOT_POSTCODE_TO_UNIVERSE",
    }
    return result


def status(live_observation_verified: bool) -> dict[str, Any]:
    """Return truthful architecture and delivery state for Weather Intelligence."""

    return {
        "name": "OAP Weather Intelligence",
        "architecture_passed": True,
        "component_count": len(COMPONENTS),
        "components": COMPONENTS,
        "live_observation_verified": bool(live_observation_verified),
        "the_spot_connected": True,
        "spatial_binding": "POSTCODE_TO_UNIVERSE",
        "source_mode": "external_live_bootstrap",
        "first_party_observation_ready": False,
        "external_dependency_present": True,
        "ready": bool(live_observation_verified),
        "truth_boundary": (
            "Live observations currently depend on bounded external no-key feeds; "
            "the final OAP-owned observation network is not yet operational."
        ),
    }
