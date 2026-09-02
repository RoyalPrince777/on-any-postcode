"""No-key location hierarchy and weather lookups with bounded safe I/O."""

from __future__ import annotations

import json
import re
import threading
import time
from typing import Any
from urllib import parse as urlparse
from urllib import request as urlrequest

from . import earth_intelligence, weather_intelligence

MAX_RESPONSE_BYTES = 128 * 1024
LOOKUP_TIMEOUT_SECONDS = 6
CACHE_SECONDS = 300
SPATIAL_LEVELS = (
    "postcode",
    "borough",
    "county",
    "country",
    "continent",
    "global",
    "universe",
)
_UK_POSTCODE = re.compile(
    r"^(?:GIR\s?0AA|[A-Z]{1,2}\d[A-Z\d]?\s?\d[A-Z]{2})$", re.IGNORECASE
)
_CACHE: dict[str, tuple[float, dict[str, Any]]] = {}
_CACHE_LOCK = threading.Lock()
_PROVIDER_STATE_LOCK = threading.Lock()
_PROVIDER_SUCCESS: dict[str, float] = {}
_PROVIDER_ERROR: dict[str, str] = {}
_CONTINENT_CODES = {
    "Africa": frozenset(
        ["DZ", "AO", "BJ", "BW", "BF", "BI", "CV", "CM", "CF", "TD", "KM", "CG", "CD", "CI", "DJ", "EG", "GQ", "ER", "SZ", "ET", "GA", "GM", "GH", "GN", "GW", "KE", "LS", "LR", "LY", "MG", "MW", "ML", "MR", "MU", "MA", "MZ", "NA", "NE", "NG", "RE", "RW", "SH", "ST", "SN", "SC", "SL", "SO", "ZA", "SS", "SD", "TZ", "TG", "TN", "UG", "EH", "ZM", "ZW", "YT"]
    ),
    "Asia": frozenset(
        ["AF", "AM", "AZ", "BH", "BD", "BT", "BN", "KH", "CN", "CY", "GE", "HK", "IN", "ID", "IR", "IQ", "IL", "JP", "JO", "KZ", "KP", "KR", "KW", "KG", "LA", "LB", "MO", "MY", "MV", "MN", "MM", "NP", "OM", "PK", "PS", "PH", "QA", "SA", "SG", "LK", "SY", "TW", "TJ", "TH", "TL", "TR", "TM", "AE", "UZ", "VN", "YE"]
    ),
    "Europe": frozenset(
        ["AX", "AL", "AD", "AT", "BY", "BE", "BA", "BG", "HR", "CZ", "DK", "EE", "FO", "FI", "FR", "DE", "GI", "GR", "GG", "HU", "IS", "IE", "IM", "IT", "JE", "LV", "LI", "LT", "LU", "MT", "MD", "MC", "ME", "NL", "MK", "NO", "PL", "PT", "RO", "RU", "SM", "RS", "SK", "SI", "ES", "SJ", "SE", "CH", "UA", "GB", "VA", "XK"]
    ),
    "North America": frozenset(
        ["AI", "AG", "AW", "BS", "BB", "BZ", "BM", "BQ", "CA", "KY", "CR", "CU", "CW", "DM", "DO", "SV", "GL", "GD", "GP", "GT", "HT", "HN", "JM", "MQ", "MX", "MS", "NI", "PA", "PR", "BL", "KN", "LC", "MF", "PM", "VC", "SX", "TT", "TC", "US", "VG", "VI"]
    ),
    "South America": frozenset(
        ["AR", "BO", "BR", "CL", "CO", "EC", "FK", "GF", "GY", "PY", "PE", "SR", "UY", "VE"]
    ),
    "Oceania": frozenset(
        ["AS", "AU", "CX", "CC", "CK", "FJ", "PF", "GU", "KI", "MH", "FM", "NR", "NC", "NZ", "NU", "NF", "MP", "PW", "PG", "PN", "WS", "SB", "TK", "TO", "TV", "UM", "VU", "WF"]
    ),
    "Antarctica": frozenset(["AQ", "BV", "GS", "HM", "TF"]),
}


class LocationUnavailable(RuntimeError):
    """Raised when a location provider cannot return a bounded valid answer."""


def _continent(country_code: object) -> str:
    code = str(country_code or "").strip().upper()
    for continent, codes in _CONTINENT_CODES.items():
        if code in codes:
            return continent
    return "World"


def _with_spatial_tiers(location: dict[str, Any]) -> dict[str, Any]:
    """Complete every resolved place with OAP's local-to-Universe contract."""

    result = dict(location)
    result["global"] = "Global"
    result["universe"] = "Universe"
    result["hierarchy"] = tuple(
        {"level": level, "value": str(result.get(level) or "")}
        for level in SPATIAL_LEVELS
    )
    return result


def _cached(key: str) -> dict[str, Any] | None:
    with _CACHE_LOCK:
        item = _CACHE.get(key)
        if item and item[0] > time.monotonic():
            return item[1]
        if item:
            _CACHE.pop(key, None)
    return None


def _store(key: str, value: dict[str, Any]) -> dict[str, Any]:
    with _CACHE_LOCK:
        _CACHE[key] = (time.monotonic() + CACHE_SECONDS, value)
        if len(_CACHE) > 256:
            oldest = min(_CACHE, key=lambda item: _CACHE[item][0])
            _CACHE.pop(oldest, None)
    return value


def _json(url: str, expected_host: str) -> dict[str, Any]:
    parsed = urlparse.urlparse(url)
    if parsed.scheme != "https" or parsed.hostname != expected_host:
        raise ValueError("unapproved_location_provider")
    request = urlrequest.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "ON-ANY-POSTCODE-Location/1.0",
        },
    )
    try:
        with urlrequest.urlopen(request, timeout=LOOKUP_TIMEOUT_SECONDS) as response:
            final = urlparse.urlparse(response.geturl())
            if final.scheme != "https" or final.hostname != expected_host:
                raise LocationUnavailable("location_provider_redirect_rejected")
            body = response.read(MAX_RESPONSE_BYTES + 1)
    except (OSError, TimeoutError) as exc:
        with _PROVIDER_STATE_LOCK:
            _PROVIDER_ERROR[expected_host] = type(exc).__name__
        raise LocationUnavailable("location_provider_unavailable") from exc
    if len(body) > MAX_RESPONSE_BYTES:
        raise LocationUnavailable("location_response_too_large")
    try:
        value = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise LocationUnavailable("invalid_location_response") from exc
    if not isinstance(value, dict):
        raise LocationUnavailable("invalid_location_response")
    with _PROVIDER_STATE_LOCK:
        _PROVIDER_SUCCESS[expected_host] = time.time()
        _PROVIDER_ERROR.pop(expected_host, None)
    return value


def lookup(value: object) -> dict[str, Any]:
    """Resolve a postcode or place into OAP's seven-tier spatial hierarchy."""

    query = " ".join(str(value or "").strip().split())[:120]
    if len(query) < 2:
        raise ValueError("location_required")
    cache_key = "location:" + query.casefold()
    if cached := _cached(cache_key):
        return cached

    compact = query.replace(" ", "").upper()
    if _UK_POSTCODE.fullmatch(query.upper()):
        url = "https://api.postcodes.io/postcodes/" + urlparse.quote(compact)
        payload = _json(url, "api.postcodes.io")
        result = payload.get("result")
        if not isinstance(result, dict):
            raise ValueError("location_not_found")
        normalized = _with_spatial_tiers(
            {
                "query": query,
                "postcode": str(result.get("postcode") or query).upper(),
                "borough": str(result.get("admin_district") or ""),
                "county": str(
                    result.get("admin_county")
                    or result.get("region")
                    or result.get("parish")
                    or ""
                ),
                "country": str(result.get("country") or "United Kingdom"),
                "continent": "Europe",
                "latitude": float(result["latitude"]),
                "longitude": float(result["longitude"]),
                "provider": "UK postcode service",
            }
        )
        return _store(cache_key, normalized)

    parameters = urlparse.urlencode(
        {"name": query, "count": 1, "language": "en", "format": "json"}
    )
    payload = _json(
        "https://geocoding-api.open-meteo.com/v1/search?" + parameters,
        "geocoding-api.open-meteo.com",
    )
    results = payload.get("results")
    if not isinstance(results, list) or not results or not isinstance(results[0], dict):
        raise ValueError("location_not_found")
    item = results[0]
    normalized = _with_spatial_tiers(
        {
            "query": query,
            "postcode": str(
                item.get("postcodes", [""])[0] if item.get("postcodes") else ""
            ),
            "borough": str(item.get("admin3") or item.get("name") or ""),
            "county": str(item.get("admin2") or item.get("admin1") or ""),
            "country": str(item.get("country") or ""),
            "continent": _continent(item.get("country_code")),
            "latitude": float(item["latitude"]),
            "longitude": float(item["longitude"]),
            "provider": "Global place service",
        }
    )
    return _store(cache_key, normalized)


def weather(latitude: object, longitude: object) -> dict[str, Any]:
    """Load and interpret a bounded current forecast for resolved coordinates."""

    try:
        lat = round(float(latitude), 5)
        lon = round(float(longitude), 5)
    except (TypeError, ValueError) as exc:
        raise ValueError("invalid_coordinates") from exc
    if not -90 <= lat <= 90 or not -180 <= lon <= 180:
        raise ValueError("invalid_coordinates")
    cache_key = f"weather:{lat}:{lon}"
    if cached := _cached(cache_key):
        return cached
    parameters = urlparse.urlencode(
        {
            "latitude": lat,
            "longitude": lon,
            "current": (
                "temperature_2m,apparent_temperature,precipitation,"
                "weather_code,wind_speed_10m"
            ),
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max",
            "forecast_days": 3,
            "timezone": "auto",
        }
    )
    payload = _json(
        "https://api.open-meteo.com/v1/forecast?" + parameters,
        "api.open-meteo.com",
    )
    current = payload.get("current")
    daily = payload.get("daily")
    if not isinstance(current, dict) or not isinstance(daily, dict):
        raise LocationUnavailable("invalid_weather_response")
    observation = {
        "temperature": current.get("temperature_2m"),
        "feels_like": current.get("apparent_temperature"),
        "precipitation": current.get("precipitation"),
        "weather_code": current.get("weather_code"),
        "wind_speed": current.get("wind_speed_10m"),
        "time": str(current.get("time") or ""),
        "days": [
            {
                "date": str(date),
                "maximum": maximum,
                "minimum": minimum,
                "rain_chance": rain,
            }
            for date, maximum, minimum, rain in zip(
                daily.get("time", []),
                daily.get("temperature_2m_max", []),
                daily.get("temperature_2m_min", []),
                daily.get("precipitation_probability_max", []),
                strict=False,
            )
        ][:3],
        "provider": "Live weather service",
    }
    return _store(cache_key, weather_intelligence.enrich(observation))


def lookup_with_weather(value: object) -> dict[str, Any]:
    location = lookup(value)
    local_weather = weather(location["latitude"], location["longitude"])
    return {
        **location,
        "weather": local_weather,
        "earth_intelligence": earth_intelligence.compose(location, local_weather),
    }


def status() -> dict[str, object]:
    """Return real provider delivery evidence without network calls on a GET."""

    with _PROVIDER_STATE_LOCK:
        successes = dict(_PROVIDER_SUCCESS)
        errors = dict(_PROVIDER_ERROR)
    postcode_verified = "api.postcodes.io" in successes
    global_verified = "geocoding-api.open-meteo.com" in successes
    weather_verified = "api.open-meteo.com" in successes
    intelligence = weather_intelligence.status(weather_verified)
    earth = earth_intelligence.status(weather_ready=bool(intelligence["ready"]))
    return {
        "postcode_provider_verified": postcode_verified,
        "global_provider_verified": global_verified,
        "weather_provider_verified": weather_verified,
        "weather_intelligence": intelligence,
        "weather_intelligence_architecture_passed": bool(intelligence["architecture_passed"]),
        "weather_intelligence_component_count": int(intelligence["component_count"]),
        "weather_intelligence_ready": bool(intelligence["ready"]),
        "weather_intelligence_first_party_ready": bool(intelligence["first_party_observation_ready"]),
        "earth_intelligence": earth,
        "earth_intelligence_architecture_passed": bool(earth["architecture_passed"]),
        "earth_intelligence_component_count": int(earth["component_count"]),
        "earth_intelligence_ready": bool(earth["ready"]),
        "earth_intelligence_fully_operational": bool(earth["fully_operational"]),
        "spatial_levels": SPATIAL_LEVELS,
        "spatial_contract": "POSTCODE_TO_UNIVERSE",
        "bounded_timeout": LOOKUP_TIMEOUT_SECONDS,
        "cache_seconds": CACHE_SECONDS,
        "last_success_epoch": {
            host: int(timestamp) for host, timestamp in successes.items()
        },
        "errors": errors,
        "ready": postcode_verified and global_verified and weather_verified,
    }
