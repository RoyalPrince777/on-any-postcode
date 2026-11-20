"""Founder-private SMI Third Eye: bounded, attributable public Earth observations.

This is an adapter to existing Earth/Map Intelligence, not a second globe,
camera pipeline, autonomous surveillance system or public dashboard. It does
not infer live feeds from a provider catalogue or user-supplied URLs.
"""
from __future__ import annotations

import csv
import io
import json
import math
import os
import re
import threading
import time
from datetime import UTC, date, datetime, timedelta
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
# Public CR4 district reference, not a device or personal location.
CR4_CENTRE_LAT = 51.4026
CR4_CENTRE_LON = -0.14516
TFL_PAGE_SIZE = 20
ADSB_LONDON_URL = "https://api.adsb.lol/v2/lat/51.4026/lon/-0.14516/dist/80"
ISS_POSITION_URL = "https://api.wheretheiss.at/v1/satellites/25544"
CELESTRAK_ISS_URL = "https://celestrak.org/NORAD/elements/gp.php?CATNR=25544&FORMAT=CSV"
NASA_GIBS_WMS = "https://gibs.earthdata.nasa.gov/wms/epsg4326/best/wms.cgi"
NASA_LAYER = "MODIS_Terra_CorrectedReflectance_TrueColor"
THIRD_EYE_JSON_LIMIT = 600_000
THIRD_EYE_IMAGE_LIMIT = 2_000_000
_THIRD_EYE_SOURCE_LOCK = threading.Lock()
_THIRD_EYE_SOURCE_CACHE: dict[str, tuple[float, Any]] = {}

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
            "aircraft": {
                "state": "adsb_lol_on_demand_adapter_unverified",
                "provider": "adsb.lol",
                "live_feed_proven": False,
                "source_license": "ODbL-1.0",
                "location_scope": "public_adsb_around_london",
            },
            "satellites": {
                "state": "iss_and_celestrak_on_demand_adapters_unverified",
                "providers": ["Where the ISS at", "CelesTrak"],
                "live_feed_proven": False,
                "orbital_position_calc_verified": False,
            },
            "satellite_imagery": {
                "state": "nasa_gibs_on_demand_adapter_unverified",
                "provider": "NASA GIBS",
                "full_resolution_verified": False,
                "exact_capture_date_proven": False,
            },
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


def _distance_from_cr4_km(latitude: float, longitude: float) -> float:
    """Approximate ground distance from the public CR4 district centre."""
    lat1, lat2 = math.radians(CR4_CENTRE_LAT), math.radians(latitude)
    dlat = lat2 - lat1
    dlon = math.radians(longitude - CR4_CENTRE_LON)
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 6371.0 * 2.0 * math.asin(min(1.0, math.sqrt(a)))


def london_jamcams(*, search: str = "", page: int = 1, radius_km: int = 0) -> dict[str, Any]:
    """Founder-triggered TfL catalogue, CR4-first and fully paginated.

    Radius 0 means all available publicly published London cameras; 5/15/30
    focus CR4 surroundings. Never derive this centre from device location.
    """
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
    query = " ".join(search.casefold().split())[:80]
    # CR4 and Mitcham select the fixed locality anchor, not name matching.
    if query in {"cr4", "mitcham", "london", "cr4 mitcham"}:
        query = ""
    page = max(1, min(int(page), 1000))
    radius_km = int(radius_km)
    if radius_km not in {0, 5, 15, 30}:
        raise ValueError("invalid_camera_radius")
    ranked = sorted(
        (
            {
                **camera,
                "distance_km": round(_distance_from_cr4_km(
                    camera["latitude"], camera["longitude"]
                ), 1),
            }
            for camera in cameras
            if not query or query in camera["name"].casefold()
        ),
        key=lambda camera: (
            _distance_from_cr4_km(camera["latitude"], camera["longitude"]),
            camera["id"],
        ),
    )
    if radius_km:
        ranked = [camera for camera in ranked if camera["distance_km"] <= radius_km]
    total_matching = len(ranked)
    offset = (page - 1) * TFL_PAGE_SIZE
    page_cameras = ranked[offset:offset + TFL_PAGE_SIZE]
    return {
        "provider": "Transport for London (TfL)",
        "availability": "catalogue_received",
        "source_verified": True,
        "live_frame_verified": False,
        "frame_capture_time_verified": False,
        "continuous_live_video": False,
        "refresh_guidance_seconds": 300,
        "region": "London",
        "cameras": page_cameras,
        "total_available_catalogued": len(cameras),
        "total_matching": total_matching,
        "page": page,
        "page_size": TFL_PAGE_SIZE,
        "has_more": offset + len(page_cameras) < total_matching,
        "has_previous": page > 1,
        "radius_km": radius_km,
        "sort": "distance_from_cr4_nearest_first",
        "origin": {"label": "CR4 / Mitcham district", "latitude": CR4_CENTRE_LAT,
                   "longitude": CR4_CENTRE_LON, "precision": "district_reference_not_device"},
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


# On-demand, fixed-destination public data adapters. Every fetch has an explicit
# provider identity, a size/time bound and a source timestamp where available.
# Data is never presented as a private surveillance feed or authority to act.
def _source_cache(key: str) -> Any | None:
    with _THIRD_EYE_SOURCE_LOCK:
        item = _THIRD_EYE_SOURCE_CACHE.get(key)
        if item and item[0] > time.monotonic():
            return item[1]
    return None


def _store_source_cache(key: str, data: Any, seconds: int) -> Any:
    with _THIRD_EYE_SOURCE_LOCK:
        _THIRD_EYE_SOURCE_CACHE[key] = (time.monotonic() + seconds, data)
    return data


def _fixed_download(url: str, accept: str, limit: int, timeout: int = 6) -> tuple[bytes, str]:
    request = Request(url, headers={
        "Accept": accept,
        "User-Agent": "OAP-SMI-ThirdEye/1",
    })
    with urlopen(request, timeout=timeout) as response:
        if response.status != 200 or response.geturl() != url:
            raise ValueError("untrusted_source_redirect_or_status")
        raw = response.read(limit + 1)
        content_type = response.headers.get_content_type()
    if not raw or len(raw) > limit:
        raise ValueError("invalid_source_payload_size")
    return raw, content_type


def _valid_finite_number(value: Any, low: float, high: float) -> bool:
    return (not isinstance(value, bool) and isinstance(value, (int, float))
            and math.isfinite(value) and low <= value <= high)


def parse_london_aircraft(payload: Any, *, now: datetime | None = None) -> dict[str, Any]:
    """Provider-reported positions, bounded by source time and valid geography."""
    if not isinstance(payload, dict):
        raise TypeError("invalid_adsb_response")
    epoch = payload.get("now")
    aircraft = payload.get("ac")
    if not _valid_finite_number(epoch, 1, 4_000_000_000) or not isinstance(aircraft, list):
        raise ValueError("unattributed_adsb_response")
    current = (now or datetime.now(UTC)).timestamp()
    source_age = current - float(epoch)
    freshness = "fresh" if -30 <= source_age <= 150 else "stale"
    results: list[dict[str, Any]] = []
    for item in aircraft[:400]:
        if not isinstance(item, dict):
            continue
        lat, lon = item.get("lat"), item.get("lon")
        seen = item.get("seen_pos")
        if not (_valid_finite_number(lat, 50.85, 52.05)
                and _valid_finite_number(lon, -1.0, 0.75)
                and _valid_finite_number(seen, 0, 120)):
            continue
        age = source_age + float(seen)
        if age < -30 or age > 180:
            continue
        flight = str(item.get("flight") or "").strip()[:10]
        results.append({
            "callsign": flight or "Aircraft (unlabelled)",
            "latitude": round(float(lat), 4),
            "longitude": round(float(lon), 4),
            "observed_at": datetime.fromtimestamp(
                float(epoch) - float(seen), tz=UTC
            ).isoformat().replace("+00:00", "Z"),
            "position_age_seconds": round(max(0.0, age)),
            "altitude": str(item.get("alt_baro") or "unavailable")[:16],
            "source": "adsb.lol",
        })
        if len(results) >= 40:
            break
    return {
        "provider": "adsb.lol",
        "provider_license": "ODbL-1.0",
        "attribution": "Aircraft data © adsb.lol contributors (ODbL 1.0)",
        "provider_timestamp": datetime.fromtimestamp(float(epoch), tz=UTC).isoformat().replace("+00:00", "Z"),
        "freshness": freshness,
        "live_claim_allowed": freshness == "fresh" and bool(results),
        "positions": results,
        "coverage": "Public receiver reports around London / CR4; incomplete, not surveillance",
        "individual_tracking": False,
    }


def london_aircraft() -> dict[str, Any]:
    """One on-demand London ADS-B observation; cached to respect free quotas."""
    cached = _source_cache("london_aircraft")
    if cached is not None:
        return cached
    try:
        raw, content_type = _fixed_download(ADSB_LONDON_URL, "application/json", THIRD_EYE_JSON_LIMIT)
        if content_type != "application/json":
            raise ValueError("wrong_aircraft_content_type")
        result = parse_london_aircraft(json.loads(raw.decode("utf-8")))
        return _store_source_cache("london_aircraft", result, 180)
    except (HTTPError, URLError, TimeoutError, OSError, ValueError, TypeError, UnicodeError, OverflowError):
        return {"provider": "adsb.lol", "freshness": "unavailable",
                "live_claim_allowed": False, "positions": [],
                "attribution": "Aircraft data © adsb.lol contributors (ODbL 1.0)",
                "coverage": "Unverified; no aircraft inferred"}


def parse_iss_position(payload: Any, *, now: datetime | None = None) -> dict[str, Any]:
    """Timestamped ISS position only; not a general satellite surveillance feed."""
    if not isinstance(payload, dict) or payload.get("id") != 25544:
        raise ValueError("unverified_iss_identity")
    timestamp = payload.get("timestamp")
    lat, lon = payload.get("latitude"), payload.get("longitude")
    if (not _valid_finite_number(timestamp, 1, 4_000_000_000)
            or not _valid_finite_number(lat, -90, 90)
            or not _valid_finite_number(lon, -180, 180)):
        raise ValueError("unverified_iss_observation")
    age = (now or datetime.now(UTC)).timestamp() - float(timestamp)
    if not -30 <= age <= 3600:
        raise ValueError("iss_time_outside_allowed_window")
    fresh = age <= 180
    altitude = payload.get("altitude")
    return {
        "provider": "Where the ISS at",
        "satellite": "International Space Station (NORAD 25544)",
        "observed_at": datetime.fromtimestamp(float(timestamp), tz=UTC).isoformat().replace("+00:00", "Z"),
        "latitude": round(float(lat), 4), "longitude": round(float(lon), 4),
        "altitude_km": round(float(altitude), 1) if _valid_finite_number(altitude, 100, 1000) else None,
        "freshness": "fresh" if fresh else "stale",
        "live_claim_allowed": fresh,
        "is_over_london": False,  # Must not infer visibility or overflight.
        "scope": "ISS only; calculated positions from orbital data, not a camera",
    }


def iss_position() -> dict[str, Any]:
    cached = _source_cache("iss_position")
    if cached is not None:
        return cached
    try:
        raw, kind = _fixed_download(ISS_POSITION_URL, "application/json", 64_000)
        if kind != "application/json":
            raise ValueError("wrong_iss_content_type")
        return _store_source_cache(
            "iss_position", parse_iss_position(json.loads(raw.decode("utf-8"))), 45
        )
    except (HTTPError, URLError, TimeoutError, OSError, ValueError, TypeError, UnicodeError, OverflowError):
        return {"provider": "Where the ISS at", "freshness": "unavailable",
                "live_claim_allowed": False, "satellite": "ISS",
                "scope": "No position can be claimed"}


def parse_celestrak_iss_csv(raw: bytes) -> dict[str, Any]:
    """Latest published ISS mean orbital elements; not propagated coordinates."""
    text = raw.decode("utf-8-sig")
    rows = list(csv.DictReader(io.StringIO(text)))
    row = next((x for x in rows if str(x.get("NORAD_CAT_ID") or "") == "25544"), None)
    if row is None:
        raise ValueError("iss_orbital_elements_not_found")
    epoch = str(row.get("EPOCH") or "").strip()
    try:
        observation = datetime.fromisoformat(epoch.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError("invalid_celestrak_epoch") from error
    if observation.tzinfo is None:
        observation = observation.replace(tzinfo=UTC)
    age = (datetime.now(UTC) - observation.astimezone(UTC)).total_seconds()
    if age < -60 or age > 14 * 86400:
        raise ValueError("stale_or_future_orbit_elements")
    elements: dict[str, float] = {}
    for field in ("MEAN_MOTION", "ECCENTRICITY", "INCLINATION"):
        try:
            value = float(row.get(field) or "")
        except ValueError as error:
            raise ValueError("invalid_orbital_element") from error
        if not math.isfinite(value):
            raise ValueError("nonfinite_orbital_element")
        elements[field.lower()] = round(value, 6)
    return {
        "provider": "CelesTrak",
        "attribution": "CelesTrak / current GP orbital element set",
        "satellite": "ISS (NORAD 25544)",
        "element_epoch": observation.astimezone(UTC).isoformat().replace("+00:00", "Z"),
        "elements": elements,
        "live_claim_allowed": False,
        "position_propagated": False,
        "note": "Published orbit elements, not an automatically calculated ground position",
    }


def iss_orbital_elements() -> dict[str, Any]:
    """CelesTrak GP CSV, cached >=2h to comply with their update schedule."""
    cached = _source_cache("celestrak_iss")
    if cached is not None:
        return cached
    try:
        raw, kind = _fixed_download(CELESTRAK_ISS_URL, "text/csv, text/plain", 80_000)
        if kind not in {"text/plain", "text/csv", "application/octet-stream"}:
            raise ValueError("wrong_celestrak_content_type")
        result = parse_celestrak_iss_csv(raw)
    except (HTTPError, URLError, TimeoutError, OSError, ValueError, TypeError, UnicodeError, OverflowError):
        result = {"provider": "CelesTrak", "live_claim_allowed": False,
                  "status": "unavailable", "position_propagated": False}
    return _store_source_cache("celestrak_iss", result, 7200)


def _nasa_day(raw: object) -> str:
    if not isinstance(raw, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", raw):
        raise ValueError("invalid_image_date")
    try:
        selected = date.fromisoformat(raw)
    except ValueError as error:
        raise ValueError("invalid_image_date") from error
    if not date(2000, 1, 1) <= selected <= datetime.now(UTC).date() - timedelta(days=1):
        raise ValueError("image_date_outside_range")
    return raw


def nasa_london_imagery(day: object) -> bytes | None:
    """Fixed London-bounds NASA GIBS true-colour map. Never live satellite video."""
    selected = _nasa_day(day)
    cache_key = "nasa_gibs_" + selected
    cached = _source_cache(cache_key)
    if cached is not None:
        return cached
    params = {
        "SERVICE": "WMS", "VERSION": "1.1.1", "REQUEST": "GetMap",
        "LAYERS": NASA_LAYER, "STYLES": "", "FORMAT": "image/jpeg",
        "SRS": "EPSG:4326", "BBOX": "-0.55,51.25,0.25,51.72",
        "WIDTH": "768", "HEIGHT": "512", "TIME": selected,
    }
    url = NASA_GIBS_WMS + "?" + urlencode(params)
    try:
        raw, kind = _fixed_download(url, "image/jpeg", THIRD_EYE_IMAGE_LIMIT, 9)
        if kind != "image/jpeg" or not raw.startswith(b"\xff\xd8\xff"):
            raise ValueError("wrong_nasa_image_type")
        return _store_source_cache(cache_key, raw, 1200)
    except (HTTPError, URLError, TimeoutError, OSError, ValueError, TypeError, UnicodeError, OverflowError):
        return None
