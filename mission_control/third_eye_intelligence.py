"""Founder-private SMI Third Eye: bounded, attributable public Earth observations.

This is an adapter to existing Earth/Map Intelligence, not a second globe,
camera pipeline, autonomous surveillance system or public dashboard. It does
not infer live feeds from a provider catalogue or user-supplied URLs.
"""
from __future__ import annotations

import json
import math
import os
import re
import threading
import time
from datetime import UTC, datetime
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

USGS_URL = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson"
MAX_RESPONSE_BYTES = 750_000
MAX_EVENTS = 25
FRESH_SECONDS = 15 * 60
TFL_JAMCAM_URL = "https://api.tfl.gov.uk/Place/Type/JamCam"
TFL_IMAGE_PREFIX = "https://s3-eu-west-1.amazonaws.com/jamcams.tfl.gov.uk/"
TFL_TERMS = "https://tfl.gov.uk/corporate/terms-and-conditions/transport-data-service"
TFL_ID = re.compile(r"^\d{5}\.\d{5}$")
TFL_MEDIA_LIMIT = 800_000
TFL_VIDEO_LIMIT = 12_000_000
TFL_CATALOGUE_LIMIT = 5_000_000
TFL_CACHE_SECONDS = 240
_TFL_LOCK = threading.Lock()
_TFL_CACHE: tuple[float, list[dict[str, Any]]] | None = None


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
            "public_cameras": {
                "state": "tfl_on_demand_adapter_unverified",
                "provider": "Transport for London (TfL)",
                "mode": "public_traffic_stills_not_continuous_video",
                "live_feed_proven": False,
                "frame_capture_time_proven": False,
                "region": "London",
                "terms_url": TFL_TERMS,
            },
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
        raise TypeError("missing_feed_evidence")
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


def parse_london_jamcams(payload: Any) -> list[dict[str, Any]]:
    """Extract only available public TfL road cameras with a vetted media host."""
    if not isinstance(payload, list):
        raise TypeError("invalid_tfl_camera_catalogue")
    cameras: list[dict[str, Any]] = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        raw_id = str(item.get("id") or "").removeprefix("JamCams_")
        if TFL_ID.fullmatch(raw_id) is None:
            continue
        properties = item.get("additionalProperties") or ()
        if not isinstance(properties, list):
            continue
        attrs = {
            prop.get("key"): prop.get("value")
            for prop in properties
            if isinstance(prop, dict) and isinstance(prop.get("key"), str)
        }
        if str(attrs.get("available") or "").lower() != "true":
            continue
        url = str(attrs.get("imageUrl") or "")
        if url != f"{TFL_IMAGE_PREFIX}{raw_id}.jpg":
            continue
        video_url = str(attrs.get("videoUrl") or "")
        clip_available = video_url == f"{TFL_IMAGE_PREFIX}{raw_id}.mp4"
        lat, lon = item.get("lat"), item.get("lon")
        if any(
            isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v)
            for v in (lat, lon)
        ):
            continue
        if not (51.2 <= lat <= 51.8 and -0.7 <= lon <= 0.4):
            continue
        name = str(item.get("commonName") or raw_id).strip()[:120]
        cameras.append({
            "id": raw_id,
            "name": name,
            "clip_available": clip_available,
            "latitude": round(float(lat), 5),
            "longitude": round(float(lon), 5),
        })
    return cameras


def london_jamcams(*, search: str = "") -> dict[str, Any]:
    """Founder-triggered TfL lookup. Freshly reported cameras are not live-video proof."""
    global _TFL_CACHE
    now = time.monotonic()
    with _TFL_LOCK:
        cached = _TFL_CACHE if _TFL_CACHE and _TFL_CACHE[0] > now else None
    if cached is None:
        app_key = os.getenv("TFL_APP_KEY", "").strip()
        url = TFL_JAMCAM_URL
        if app_key:
            url += "?" + urlencode({"app_key": app_key})
        request = Request(url, headers={"Accept": "application/json", "User-Agent": "OAP-SMI-ThirdEye/1"})
        try:
            with urlopen(request, timeout=6) as response:
                if response.status != 200 or response.geturl() != url:
                    raise ValueError("unexpected_tfl_response")
                raw = response.read(TFL_CATALOGUE_LIMIT + 1)
            if len(raw) > TFL_CATALOGUE_LIMIT:
                raise ValueError("oversized_tfl_catalogue")
            cameras = parse_london_jamcams(json.loads(raw.decode("utf-8")))
            if not cameras:
                raise ValueError("no_vetted_cameras")
        except (HTTPError, URLError, TimeoutError, OSError, ValueError, TypeError, UnicodeError):
            return {
                "provider": "Transport for London (TfL)",
                "availability": "unavailable",
                "source_verified": False,
                "continuous_live_video": False,
                "cameras": [],
                "attribution": "Powered by TfL Open Data",
                "terms_url": TFL_TERMS,
            }
        with _TFL_LOCK:
            _TFL_CACHE = (time.monotonic() + TFL_CACHE_SECONDS, cameras)
    else:
        cameras = cached[1]
    query = " ".join(search.lower().split())[:80]
    if query == "london":
        query = ""
    ranked = (
        [camera for camera in cameras if query in camera["name"].lower()]
        if query
        else sorted(
            cameras,
            key=lambda camera: (camera["latitude"] - 51.5074) ** 2 +
            (camera["longitude"] + 0.1278) ** 2,
        )
    )
    return {
        "provider": "Transport for London (TfL)",
        "availability": "catalogue_received",
        "source_verified": True,
        "live_frame_verified": False,
        "frame_capture_time_verified": False,
        "continuous_live_video": False,
        "refresh_guidance_seconds": 300,
        "region": "London",
        "cameras": ranked[:15],
        "total_available_catalogued": len(cameras),
        "attribution": "Powered by TfL Open Data",
        "terms_url": TFL_TERMS,
        "note": (
            "Public TfL road-camera stills and optional short rolling clips. "
            "The source updates periodically; capture times are not independently verified."
        ),
    }


def london_jamcam_frame(camera_id: str) -> tuple[bytes, str | None] | None:
    """Retrieve one vetted camera still, never a client-supplied URL or video feed."""
    if TFL_ID.fullmatch(camera_id) is None:
        return None
    # Reconfirm the ID against the current public TfL catalogue, even after restarts.
    catalogue = london_jamcams()
    if not catalogue.get("source_verified"):
        return None
    with _TFL_LOCK:
        cached = _TFL_CACHE
        ids = {item["id"] for item in cached[1]} if cached else set()
    if camera_id not in ids:
        return None
    url = f"{TFL_IMAGE_PREFIX}{camera_id}.jpg"
    request = Request(url, headers={"Accept": "image/jpeg", "User-Agent": "OAP-SMI-ThirdEye/1"})
    try:
        with urlopen(request, timeout=5) as response:
            if response.status != 200 or response.geturl() != url:
                return None
            if response.headers.get_content_type() != "image/jpeg":
                return None
            modified = response.headers.get("Last-Modified")
            frame = response.read(TFL_MEDIA_LIMIT + 1)
        if len(frame) > TFL_MEDIA_LIMIT or not frame.startswith(b"\xff\xd8\xff"):
            return None
        return frame, modified
    except (HTTPError, URLError, TimeoutError, OSError, ValueError):
        return None


def london_jamcam_clip(camera_id: str) -> tuple[bytes, str | None] | None:
    """Read one public TfL rolling MP4 clip on explicit Founder request.

    This is short provider-published footage, not an uninterrupted live stream.
    The URL is derived exclusively from a vetted, currently-available camera.
    """
    if TFL_ID.fullmatch(camera_id) is None:
        return None
    catalogue = london_jamcams()
    if not catalogue.get("source_verified"):
        return None
    with _TFL_LOCK:
        cached = _TFL_CACHE
        matched = next(
            (
                camera for camera in cached[1]
                if camera["id"] == camera_id and camera.get("clip_available")
            ),
            None,
        ) if cached else None
    if matched is None:
        return None
    url = f"{TFL_IMAGE_PREFIX}{camera_id}.mp4"
    request = Request(url, headers={
        "Accept": "video/mp4",
        "User-Agent": "OAP-SMI-ThirdEye/1",
    })
    try:
        with urlopen(request, timeout=8) as response:
            if response.status != 200 or response.geturl() != url:
                return None
            if response.headers.get_content_type() != "video/mp4":
                return None
            last_modified = response.headers.get("Last-Modified")
            clip = response.read(TFL_VIDEO_LIMIT + 1)
        if len(clip) > TFL_VIDEO_LIMIT or len(clip) < 12 or clip[4:8] != b"ftyp":
            return None
        return clip, last_modified
    except (HTTPError, URLError, TimeoutError, OSError, ValueError):
        return None
