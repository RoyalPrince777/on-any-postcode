"""Founder-private SMI Third Eye: bounded, attributable public Earth observations.

This is an adapter to existing Earth/Map Intelligence, not a second globe,
camera pipeline, autonomous surveillance system or public dashboard. It does
not infer live feeds from a provider catalogue or user-supplied URLs.
"""
from __future__ import annotations

import json
import math
from datetime import UTC, datetime
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

USGS_URL = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson"
MAX_RESPONSE_BYTES = 750_000
MAX_EVENTS = 25
FRESH_SECONDS = 15 * 60


def status() -> dict[str, Any]:
    """No network or device capture; disclose only evidence-backed readiness."""
    return {
        "component": "SMI Third Eye",
        "placement": "SMI -> Earth Intelligence -> Map Intelligence",
        "founder_private_only": True,
        "public_route_allowed": False,
        "mode": "read_only_observation",
        "camera_view": {
            "existing_control": "SMI Face Up / Vision",
            "continuous_live_analysis_certified": False,
            "device_camera_started": False,
        },
        "sources": {
            "earthquakes": {
                "provider": "USGS",
                "endpoint": USGS_URL,
                "fetch_mode": "founder_requested_only",
                "feed_proven": False,
                "state": "unchecked",
            },
            "public_cameras": {"state": "not_connected", "live_feed_proven": False},
            "aircraft": {"state": "not_connected", "live_feed_proven": False},
            "satellites": {"state": "not_connected", "live_feed_proven": False},
            "3d_globe": {"state": "not_integrated", "render_proven": False},
        },
        "upstream_reference": {
            "project": "bilawalsidhu/gods-eye-view",
            "license": "MIT for source code only",
            "third_party_data_permission_assumed": False,
            "production_hardened_assumed": False,
            "upstream_code_imported": False,
        },
        "hidden_tracking": False,
        "universal_surveillance": False,
        "individual_tracking": False,
        "auto_recording": False,
        "location_permission_requested": False,
        "execution_granted": False,
        "founder_final_required": True,
        "full_third_eye_ready": False,
    }


def _utc_iso(milliseconds: int) -> str:
    return datetime.fromtimestamp(milliseconds / 1000, tz=UTC).isoformat().replace("+00:00", "Z")


def parse_usgs_feed(payload: Any, *, now: datetime | None = None) -> dict[str, Any]:
    """Validate USGS's fixed GeoJSON format, provenance and freshness."""
    if not isinstance(payload, dict) or payload.get("type") != "FeatureCollection":
        raise ValueError("invalid_feature_collection")
    metadata = payload.get("metadata")
    features = payload.get("features")
    if not isinstance(metadata, dict) or not isinstance(features, list):
        raise ValueError("missing_feed_evidence")
    generated = metadata.get("generated")
    if not isinstance(generated, int) or isinstance(generated, bool) or generated <= 0:
        raise ValueError("missing_feed_timestamp")
    now_utc = (now or datetime.now(UTC)).astimezone(UTC)
    elapsed = (now_utc - datetime.fromtimestamp(generated / 1000, tz=UTC)).total_seconds()
    freshness = "fresh" if 0 <= elapsed <= FRESH_SECONDS else "stale"
    events: list[dict[str, Any]] = []
    for item in features[:MAX_EVENTS]:
        if not isinstance(item, dict) or item.get("type") != "Feature":
            continue
        properties, geometry = item.get("properties"), item.get("geometry")
        if not isinstance(properties, dict) or not isinstance(geometry, dict):
            continue
        coords = geometry.get("coordinates")
        t = properties.get("time")
        magnitude = properties.get("mag")
        if not isinstance(coords, list) or len(coords) < 2:
            continue
        lon, lat = coords[:2]
        if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) for v in (lon, lat)):
            continue
        if not (-180 <= lon <= 180 and -90 <= lat <= 90):
            continue
        if not isinstance(t, int) or isinstance(t, bool) or t <= 0:
            continue
        if magnitude is not None and (
            isinstance(magnitude, bool) or not isinstance(magnitude, (int, float)) or not math.isfinite(magnitude)
        ):
            magnitude = None
        place = properties.get("place")
        events.append({
            "place": str(place)[:160] if isinstance(place, str) else "Unspecified location",
            "magnitude": round(float(magnitude), 1) if magnitude is not None else None,
            "observed_at": _utc_iso(t),
            "latitude": round(float(lat), 3),
            "longitude": round(float(lon), 3),
            "source": "USGS",
        })
    return {
        "source": "USGS Earthquake Hazards Program",
        "source_url": USGS_URL,
        "observed_feed_generated_at": _utc_iso(generated),
        "freshness": freshness,
        "live_claim_allowed": freshness == "fresh",
        "feed_verified": True,
        "display_note": "Recent USGS observations, not a live camera or universal event feed.",
        "event_count_returned": len(events),
        "events": events,
        "full_third_eye_ready": False,
    }


def latest_earthquakes() -> dict[str, Any]:
    """One explicit read, fixed public HTTPS destination, bounded time/bytes."""
    request = Request(USGS_URL, headers={"Accept": "application/geo+json, application/json", "User-Agent": "OAP-SMI-ThirdEye/1"})
    try:
        with urlopen(request, timeout=5) as response:
            if response.status != 200 or response.geturl() != USGS_URL:
                raise ValueError("unexpected_upstream_response")
            raw = response.read(MAX_RESPONSE_BYTES + 1)
        if len(raw) > MAX_RESPONSE_BYTES:
            raise ValueError("oversized_upstream_response")
        return parse_usgs_feed(json.loads(raw.decode("utf-8")))
    except (HTTPError, URLError, TimeoutError, OSError, ValueError, TypeError, UnicodeError, OverflowError):
        return {
            "source": "USGS Earthquake Hazards Program",
            "source_url": USGS_URL,
            "freshness": "unavailable",
            "feed_verified": False,
            "live_claim_allowed": False,
            "events": [],
            "full_third_eye_ready": False,
        }
