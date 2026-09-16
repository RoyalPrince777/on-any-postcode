"""First-party route-geometry proof for OAP Map Intelligence.

This adapter is stricter than the normal Movement route preview. It only accepts
an explicitly OAP-owned/self-hosted OSRM-compatible endpoint that has already
passed the routing production gates. Public/demo or external candidate hosts are
rejected. The returned geometry is proof data; it never dispatches, tracks,
charges or books anything.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any
from urllib import parse as urlparse

from . import routing


class RouteProofUnavailable(RuntimeError):
    """A first-party route cannot be proven safely."""


def _coordinate(value: object, *, minimum: float, maximum: float, name: str) -> float:
    try:
        number = round(float(value), 6)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"invalid_{name}") from exc
    if not minimum <= number <= maximum:
        raise ValueError(f"invalid_{name}")
    return number


def prove_route_geometry(
    *,
    pickup_latitude: object,
    pickup_longitude: object,
    destination_latitude: object,
    destination_longitude: object,
    profile: object = "driving",
) -> dict[str, Any]:
    """Return source-backed GeoJSON only from an approved OAP-owned route engine."""

    if routing.provider_ownership() != "oap_owned":
        raise RouteProofUnavailable("oap_owned_route_engine_required")
    if not routing.production_gate_approved():
        raise RouteProofUnavailable("routing_production_gate_required")
    base = routing._base_url()
    if not base:
        raise RouteProofUnavailable("routing_provider_not_configured")

    profile_value = str(profile or "driving").strip().casefold()
    if profile_value not in routing.ALLOWED_PROFILES:
        raise ValueError("invalid_route_profile")
    pickup_lat = _coordinate(
        pickup_latitude, minimum=-90, maximum=90, name="pickup_latitude"
    )
    pickup_lon = _coordinate(
        pickup_longitude, minimum=-180, maximum=180, name="pickup_longitude"
    )
    destination_lat = _coordinate(
        destination_latitude, minimum=-90, maximum=90, name="destination_latitude"
    )
    destination_lon = _coordinate(
        destination_longitude, minimum=-180, maximum=180, name="destination_longitude"
    )
    coordinates = f"{pickup_lon},{pickup_lat};{destination_lon},{destination_lat}"
    query = urlparse.urlencode(
        {
            "overview": "full",
            "geometries": "geojson",
            "steps": "false",
            "alternatives": "false",
        }
    )
    parsed = urlparse.urlparse(base)
    payload = routing._request_json(
        f"{base}/route/v1/{profile_value}/{coordinates}?{query}",
        expected_host=str(parsed.hostname),
    )
    if payload.get("code") != "Ok":
        raise RouteProofUnavailable("route_not_found")
    routes = payload.get("routes")
    if not isinstance(routes, list) or not routes or not isinstance(routes[0], dict):
        raise RouteProofUnavailable("invalid_routing_response")
    first = routes[0]
    geometry = first.get("geometry")
    if not isinstance(geometry, dict) or geometry.get("type") != "LineString":
        raise RouteProofUnavailable("route_geometry_required")
    points = geometry.get("coordinates")
    if not isinstance(points, list) or len(points) < 2:
        raise RouteProofUnavailable("route_geometry_required")
    try:
        distance_m = max(0.0, float(first["distance"]))
        duration_s = max(0.0, float(first["duration"]))
    except (KeyError, TypeError, ValueError) as exc:
        raise RouteProofUnavailable("invalid_routing_response") from exc

    canonical_geometry = json.dumps(
        geometry, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    )
    geometry_sha256 = hashlib.sha256(canonical_geometry.encode("utf-8")).hexdigest()
    routing._mark_success()
    return {
        "component": "OAP Map Intelligence Route Proof",
        "profile": profile_value,
        "distance_m": round(distance_m, 1),
        "duration_s": round(duration_s, 1),
        "geometry": geometry,
        "geometry_sha256": geometry_sha256,
        "source": routing.CORE_NAME,
        "engine_contract": routing.ENGINE_CONTRACT,
        "provider_ownership": "oap_owned",
        "source_timestamp": datetime.now(timezone.utc).isoformat(),
        "route_geometry_proven": True,
        "dispatch_performed": False,
        "payment_captured": False,
        "tracking_started": False,
        "booking_confirmed": False,
    }
