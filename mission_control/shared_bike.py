"""Read-only shared e-bike discovery adapter for OAP Transport.

Consumes operator-published GBFS discovery and vehicle feeds when explicitly
configured. It does not unlock, lock, reserve, charge, dispatch or modify bikes.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
from typing import Any
from urllib import parse as urlparse
from urllib import request as urlrequest

TIMEOUT_SECONDS = 6
MAX_BYTES = 2 * 1024 * 1024
MITCHAM_CENTRE = (51.4036, -0.1687)
DEFAULT_RADIUS_KM = 5.0
MAX_RADIUS_KM = 12.0

_OPERATOR_ENV = {
    "lime": "OAP_SHARED_BIKE_LIME_GBFS_URL",
    "forest": "OAP_SHARED_BIKE_FOREST_GBFS_URL",
}
_OPERATOR_AUTH_ENV = {
    "lime": "OAP_SHARED_BIKE_LIME_AUTHORIZATION",
    "forest": "OAP_SHARED_BIKE_FOREST_AUTHORIZATION",
}


class SharedBikeUnavailable(RuntimeError):
    pass


def _allowed_hosts() -> frozenset[str]:
    return frozenset(
        item.strip().casefold()
        for item in os.environ.get("OAP_SHARED_BIKE_ALLOWED_HOSTS", "").split(",")
        if item.strip()
    )


def _validated_url(value: object) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    parsed = urlparse.urlparse(raw)
    host = str(parsed.hostname or "").casefold()
    if (
        parsed.scheme != "https"
        or not host
        or parsed.username
        or parsed.password
        or parsed.fragment
        or host not in _allowed_hosts()
    ):
        return ""
    return raw


def configured_operators() -> dict[str, str]:
    return {
        operator: url
        for operator, env_name in _OPERATOR_ENV.items()
        if (url := _validated_url(os.environ.get(env_name, "")))
    }


def _operator_authorization(operator: str) -> str:
    env_name = _OPERATOR_AUTH_ENV.get(operator, "")
    return str(os.environ.get(env_name, "") if env_name else "").strip()


def _fetch_json(url: str, *, authorization: str = "") -> dict[str, Any]:
    parsed = urlparse.urlparse(url)
    expected_host = str(parsed.hostname or "").casefold()
    if not expected_host or expected_host not in _allowed_hosts():
        raise SharedBikeUnavailable("shared_bike_feed_rejected")
    headers = {
        "Accept": "application/json",
        "User-Agent": "ON-ANY-POSTCODE-SharedBike/1.0",
    }
    if authorization:
        headers["Authorization"] = authorization
    req = urlrequest.Request(url, headers=headers)
    try:
        with urlrequest.urlopen(req, timeout=TIMEOUT_SECONDS) as response:
            final = urlparse.urlparse(response.geturl())
            if (
                final.scheme != "https"
                or str(final.hostname or "").casefold() != expected_host
            ):
                raise SharedBikeUnavailable("shared_bike_redirect_rejected")
            body = response.read(MAX_BYTES + 1)
    except SharedBikeUnavailable:
        raise
    except OSError as exc:
        raise SharedBikeUnavailable("shared_bike_feed_unavailable") from exc
    if len(body) > MAX_BYTES:
        raise SharedBikeUnavailable("shared_bike_feed_too_large")
    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SharedBikeUnavailable("shared_bike_feed_invalid_json") from exc
    if not isinstance(payload, dict):
        raise SharedBikeUnavailable("shared_bike_feed_invalid")
    return payload


def _feeds(payload: dict[str, Any]) -> list[dict[str, Any]]:
    data = payload.get("data")
    if isinstance(data, dict):
        feeds = data.get("feeds")
        if isinstance(feeds, list):
            return [item for item in feeds if isinstance(item, dict)]
        for value in data.values():
            if isinstance(value, dict) and isinstance(value.get("feeds"), list):
                return [item for item in value["feeds"] if isinstance(item, dict)]
    return []


def _vehicle_feed_url(discovery_url: str, discovery: dict[str, Any]) -> str:
    names = ("vehicle_status", "free_bike_status")
    for item in _feeds(discovery):
        if str(item.get("name") or "") in names:
            return _validated_url(item.get("url"))
    raise SharedBikeUnavailable("shared_bike_vehicle_feed_missing")


def _vehicles(payload: dict[str, Any]) -> list[dict[str, Any]]:
    data = payload.get("data")
    if not isinstance(data, dict):
        return []
    for key in ("vehicles", "bikes"):
        value = data.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
    for value in data.values():
        if isinstance(value, dict):
            for key in ("vehicles", "bikes"):
                items = value.get(key)
                if isinstance(items, list):
                    return [item for item in items if isinstance(item, dict)]
    return []


def _distance_km(lat: float, lon: float, target_lat: float, target_lon: float) -> float:
    radius = 6371.0088
    p1 = math.radians(lat)
    p2 = math.radians(target_lat)
    dp = math.radians(target_lat - lat)
    dl = math.radians(target_lon - lon)
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return radius * 2 * math.atan2(math.sqrt(h), math.sqrt(1 - h))


def _public_vehicle_id(operator: str, raw_id: object) -> str:
    digest = hashlib.sha256(f"{operator}:{raw_id}".encode()).hexdigest()[:12]
    return f"oap-bike-{digest}"


def _normalize_vehicle(
    operator: str,
    vehicle: dict[str, Any],
    *,
    centre_lat: float,
    centre_lon: float,
    radius_km: float,
    source: str = "operator_public_gbfs",
) -> dict[str, Any] | None:
    try:
        lat = float(vehicle.get("lat"))
        lon = float(vehicle.get("lon"))
    except (TypeError, ValueError):
        return None
    distance = _distance_km(centre_lat, centre_lon, lat, lon)
    if distance > radius_km:
        return None
    raw_id = vehicle.get("vehicle_id") or vehicle.get("bike_id") or vehicle.get("id")
    rental_uris = vehicle.get("rental_uris") if isinstance(vehicle.get("rental_uris"), dict) else {}
    return {
        "oap_vehicle_id": _public_vehicle_id(operator, raw_id or f"{lat}:{lon}"),
        "operator": operator,
        "latitude": round(lat, 6),
        "longitude": round(lon, 6),
        "distance_km": round(distance, 2),
        "reserved": bool(vehicle.get("is_reserved")),
        "disabled": bool(vehicle.get("is_disabled")),
        "rental_uri_android": str(rental_uris.get("android") or "")[:500],
        "rental_uri_ios": str(rental_uris.get("ios") or "")[:500],
        "source": source,
        "read_only": True,
        "unlock_performed": False,
        "lock_performed": False,
        "reservation_performed": False,
        "payment_performed": False,
        "motor_control_performed": False,
    }


def nearby_mitcham(*, radius_km: object = DEFAULT_RADIUS_KM) -> dict[str, Any]:
    try:
        radius = float(radius_km)
    except (TypeError, ValueError) as exc:
        raise ValueError("invalid_radius_km") from exc
    if not 0.5 <= radius <= MAX_RADIUS_KM:
        raise ValueError("invalid_radius_km")

    operators = configured_operators()
    results: list[dict[str, Any]] = []
    operator_state: dict[str, dict[str, Any]] = {}
    for operator, discovery_url in operators.items():
        authorization = _operator_authorization(operator)
        source = "operator_authorized_gbfs" if authorization else "operator_public_gbfs"
        try:
            discovery = _fetch_json(discovery_url, authorization=authorization)
            vehicle_url = _vehicle_feed_url(discovery_url, discovery)
            payload = _fetch_json(vehicle_url, authorization=authorization)
            before = len(results)
            for vehicle in _vehicles(payload):
                normalized = _normalize_vehicle(
                    operator,
                    vehicle,
                    centre_lat=MITCHAM_CENTRE[0],
                    centre_lon=MITCHAM_CENTRE[1],
                    radius_km=radius,
                    source=source,
                )
                if normalized is not None:
                    results.append(normalized)
            operator_state[operator] = {
                "connected": True,
                "nearby_count": len(results) - before,
                "feed_type": "GBFS",
                "authorized_access": bool(authorization),
            }
        except SharedBikeUnavailable as exc:
            operator_state[operator] = {
                "connected": False,
                "nearby_count": 0,
                "error": str(exc)[:80],
                "feed_type": "GBFS",
                "authorized_access": bool(authorization),
            }

    results.sort(key=lambda item: (float(item["distance_km"]), str(item["operator"])))
    return {
        "product": "OAP Shared E-Bikes",
        "area": "Mitcham",
        "postcode": "CR4",
        "centre": {"latitude": MITCHAM_CENTRE[0], "longitude": MITCHAM_CENTRE[1]},
        "radius_km": radius,
        "configured_operator_count": len(operators),
        "operators": operator_state,
        "vehicle_count": len(results),
        "vehicles": results[:200],
        "public_discovery_only": True,
        "operator_control_authorised": False,
        "unlock_enabled": False,
        "lock_enabled": False,
        "reservation_enabled": False,
        "payment_enabled": False,
        "motor_control_enabled": False,
        "human_authority_final": True,
    }


def status() -> dict[str, Any]:
    configured = configured_operators()
    authorized = sorted(
        operator for operator in configured
        if _operator_authorization(operator)
    )
    return {
        "product": "OAP Shared E-Bikes",
        "area": "Mitcham / CR4",
        "protocol": "GBFS",
        "configured_operators": sorted(configured),
        "configured_operator_count": len(configured),
        "public_discovery_ready": True,
        "feed_configured": bool(configured),
        "authorized_access_configured": bool(authorized),
        "authorized_access_operators": authorized,
        "live_feed_connected": False,
        "operator_control_authorised": False,
        "unlock_enabled": False,
        "lock_enabled": False,
        "reservation_enabled": False,
        "payment_enabled": False,
        "motor_control_enabled": False,
        "truth_boundary": (
            "Operator-authorized or public availability and operator-provided rental links only. "
            "Authorization secrets are never returned. No bike control, reservation, billing "
            "or motor commands without explicit operator authority."
        ),
        "human_authority_final": True,
    }
