"""First-party route geometry proof for OAP Map Intelligence.

Only an explicitly OAP-owned/self-hosted OSRM-compatible endpoint can satisfy this
proof. Public demo or external routing providers remain ineligible. The proof is
read-only and never dispatches, tracks a person, books, confirms or charges.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from . import routing

MAX_GEOMETRY_POINTS = 5000


class RouteProofUnavailable(RuntimeError):
    """Raised when first-party route evidence is missing or invalid."""


def _canonical(value: object) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def _geometry_checksum(geometry: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical(geometry)).hexdigest()


def _validate_geometry(value: object) -> dict[str, Any]:
    if not isinstance(value, dict) or value.get("type") != "LineString":
        raise RouteProofUnavailable("route_geometry_linestring_required")
    coordinates = value.get("coordinates")
    if not isinstance(coordinates, list) or len(coordinates) < 2:
        raise RouteProofUnavailable("route_geometry_coordinates_required")
    if len(coordinates) > MAX_GEOMETRY_POINTS:
        raise RouteProofUnavailable("route_geometry_too_large")
    cleaned: list[list[float]] = []
    for point in coordinates:
        if not isinstance(point, list) or len(point) != 2:
            raise RouteProofUnavailable("invalid_route_geometry_point")
        try:
            longitude = round(float(point[0]), 6)
            latitude = round(float(point[1]), 6)
        except (TypeError, ValueError) as exc:
            raise RouteProofUnavailable("invalid_route_geometry_point") from exc
        if not (-180 <= longitude <= 180 and -90 <= latitude <= 90):
            raise RouteProofUnavailable("invalid_route_geometry_point")
        cleaned.append([longitude, latitude])
    return {"type": "LineString", "coordinates": cleaned}


def prove(
    *,
    pickup_latitude: object,
    pickup_longitude: object,
    destination_latitude: object,
    destination_longitude: object,
    profile: object = "driving",
) -> dict[str, Any]:
    """Return timestamped route geometry only from an approved OAP-owned engine."""

    if routing.provider_ownership() != "oap_owned":
        raise RouteProofUnavailable("oap_owned_route_engine_required")
    if not routing.production_gate_approved():
        raise RouteProofUnavailable("oap_route_engine_production_gate_required")

    base = routing._base_url()
    if not base:
        raise RouteProofUnavailable("oap_route_engine_unconfigured")
    parsed_base = routing.urlparse.urlparse(base)
    expected_host = str(parsed_base.hostname or "")
    pickup_lat = routing._coordinate(
        pickup_latitude,
        minimum=-90,
        maximum=90,
        name="pickup_latitude",
    )
    pickup_lon = routing._coordinate(
        pickup_longitude,
        minimum=-180,
        maximum=180,
        name="pickup_longitude",
    )
    destination_lat = routing._coordinate(
        destination_latitude,
        minimum=-90,
        maximum=90,
        name="destination_latitude",
    )
    destination_lon = routing._coordinate(
        destination_longitude,
        minimum=-180,
        maximum=180,
        name="destination_longitude",
    )
    normalized_profile = routing._profile(profile)
    coordinates = f"{pickup_lon},{pickup_lat};{destination_lon},{destination_lat}"
    query = routing.urlparse.urlencode(
        {
            "overview": "full",
            "geometries": "geojson",
            "steps": "false",
            "alternatives": "false",
        }
    )
    payload = routing._request_json(
        f"{base}/route/v1/{normalized_profile}/{coordinates}?{query}",
        expected_host=expected_host,
    )
    if payload.get("code") != "Ok":
        raise RouteProofUnavailable("route_not_found")
    routes = payload.get("routes")
    if not isinstance(routes, list) or not routes or not isinstance(routes[0], dict):
        raise RouteProofUnavailable("invalid_routing_response")
    first = routes[0]
    geometry = _validate_geometry(first.get("geometry"))
    try:
        distance_m = max(0.0, float(first["distance"]))
        duration_s = max(0.0, float(first["duration"]))
    except (KeyError, TypeError, ValueError) as exc:
        raise RouteProofUnavailable("invalid_routing_response") from exc

    generated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    return {
        "proof_state": "PROVEN",
        "engine": routing.CORE_NAME,
        "engine_contract": routing.ENGINE_CONTRACT,
        "provider_ownership": "oap_owned",
        "profile": normalized_profile,
        "distance_m": round(distance_m, 1),
        "duration_s": round(duration_s, 1),
        "geometry": geometry,
        "geometry_point_count": len(geometry["coordinates"]),
        "geometry_checksum_sha256": _geometry_checksum(geometry),
        "source_timestamp": generated_at,
        "third_party_route_api_used": False,
        "payment_capture": False,
        "dispatch_performed": False,
        "hidden_tracking": False,
        "human_authority_final": True,
    }


def status() -> dict[str, Any]:
    ownership = routing.provider_ownership()
    gates = routing.production_approval_state()
    return {
        "component": "OAP First-Party Route Geometry Proof",
        "provider_ownership": ownership,
        "oap_owned_endpoint": ownership == "oap_owned",
        "production_gate_approved": routing.production_gate_approved(),
        "provider_approved": gates["provider_approved"],
        "capacity_approved": gates["capacity_approved"],
        "monitoring_approved": gates["monitoring_approved"],
        "geometry_proof_ready": bool(
            ownership == "oap_owned" and routing.production_gate_approved()
        ),
        "third_party_route_api_allowed_for_proof": False,
        "mutation_enabled": False,
        "dispatch_enabled": False,
        "payment_capture_enabled": False,
        "hidden_tracking_enabled": False,
    }
