"""Runtime projection for the approved OAP Earth Intelligence world.

Earth Intelligence powers the EARTH OUR TURF place experience.  It remains one
of the seven governed Intelligence worlds, not another OAP brain or agent
family.  Weather is the first live environmental input; wider Earth domains
remain fail-closed until real sources exist.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
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



def from_owned_sensor(reading: Mapping[str, Any], *, now: datetime | None = None) -> dict[str, Any]:
    """Strict first-party Earth entry point; never accepts external observations.

    An unverified sensor reading stays unverified. Existing legacy weather and
    NASA adapters remain isolated and do not feed this entry point.
    """
    from mission_control import earth_first_party

    record = earth_first_party.intake(reading, now=now)
    return {
        "world_id": "earth",
        "source_policy": "oap_owned_sensors_only",
        "observation": record,
        "trusted_observations": 0,
        "live_environment_ready": False,
        "full_earth_runtime_ready": False,
        "can_execute": False,
        "human_authority_final": True,
    }


def from_weather(weather: Mapping[str, Any]) -> dict[str, Any]:
    """Project verified Weather Intelligence into bounded Earth context."""

    weather_signal = weather.get("intelligence")
    weather_ready = (
        isinstance(weather_signal, Mapping)
        and bool(_text(weather_signal.get("observation_time")))
        and _text(weather_signal.get("advisory_level")) != "unavailable"
    )
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



def first_party_status() -> dict[str, Any]:
    """Founder-governed Earth readiness independent of legacy weather adapters."""
    from mission_control import earth_first_party

    return {
        "name": "OAP First-Party Earth Intelligence",
        "world_id": "earth",
        "source_policy": "oap_owned_sensors_only",
        "legacy_weather_is_authoritative": False,
        "nasa_adapter_enabled": False,
        "sensor_intake": earth_first_party.status(),
        "verified_sensor_nodes": 0,
        "verified_owned_physical_servers": 0,
        "full_earth_runtime_ready": False,
        "can_execute": False,
        "human_authority_final": True,
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

# NASA Earth-observation evidence is deliberately read-only. This adapter
# accepts externally retrieved metadata; it does not fetch, execute, or grant
# authority from external sources.
def validate_earth_observation(item: Mapping[str, Any]) -> dict[str, Any]:
    """Fail closed on incomplete NASA Earthdata observation metadata."""
    from datetime import datetime
    from hashlib import sha256
    from urllib.parse import urlsplit

    required = ("observation_id", "dataset", "captured_at", "source_url", "checksum_sha256")
    values = {key: _text(item.get(key)) for key in required}
    if any(not value for value in values.values()):
        return {"valid": False, "reason": "missing_required_metadata", "can_execute": False}
    try:
        parsed = datetime.fromisoformat(values["captured_at"])
        if parsed.tzinfo is None:
            raise ValueError("timezone_required")
    except ValueError:
        return {"valid": False, "reason": "invalid_capture_time", "can_execute": False}
    url = urlsplit(values["source_url"])
    if (url.scheme != "https" or not url.hostname or url.username or url.password
            or url.hostname.lower() not in {"earthdata.nasa.gov", "data.nasa.gov", "cmr.earthdata.nasa.gov"}):
        return {"valid": False, "reason": "untrusted_source", "can_execute": False}
    digest = values["checksum_sha256"].lower()
    if len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
        return {"valid": False, "reason": "invalid_checksum", "can_execute": False}
    return {
        "valid": True,
        "observation_id": values["observation_id"][:200],
        "dataset": values["dataset"][:200],
        "captured_at": parsed.isoformat(),
        "source_url": values["source_url"],
        "checksum_sha256": digest,
        "metadata_fingerprint": sha256(
            ("|".join(values[key] for key in required)).encode("utf-8")
        ).hexdigest(),
        "source_verified": False,
        "payload_integrity_verified": False,
        "can_execute": False,
        "full_earth_runtime_ready": False,
    }


def nasa_observation_envelope(item: Mapping[str, Any], *, received_at: str) -> dict[str, Any]:
    """Project validated metadata into the existing governed World Observation model.

    Metadata alone is unverified: it cannot assert a live observation, prove
    downloaded bytes, or grant any execution permission.
    """
    from mission_control import world_observation

    checked = validate_earth_observation(item)
    if not checked["valid"]:
        raise ValueError(str(checked["reason"]))
    if not _text(received_at):
        raise ValueError("received_at_required")
    return world_observation.normalise({
        "object_id": checked["observation_id"],
        "object_type": "nasa_earth_observation_metadata",
        "evidence_class": "unverified",
        "source": checked["source_url"],
        "source_ownership": "external_public",
        "observed_at": checked["captured_at"],
        "received_at": received_at,
        "evidence": (),
        "first_party": {"software": True, "processing": True, "observation": False},
    })
