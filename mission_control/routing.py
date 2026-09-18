"""Bounded, read-only routing adapter for OAP Movement and Map Intelligence.

OAP Route Core owns the routing contract and responses. Operational Movement
remains proof-gated. Map Intelligence may request read-only route geometry and
road-network vector tiles from explicitly configured OAP-owned/self-hosted
OSRM-compatible endpoints; this never dispatches, charges, or silently tracks anyone.
"""
from __future__ import annotations

import hashlib
import json
import os
import threading
import time
from typing import Any
from urllib import parse as urlparse
from urllib import request as urlrequest

CORE_NAME = "OAP Route Core"
ENGINE_CONTRACT = "OSRM-compatible"
MAX_RESPONSE_BYTES = 512 * 1024
MAX_TILE_BYTES = 2 * 1024 * 1024
ROUTE_TIMEOUT_SECONDS = 6
ALLOWED_PROFILES = frozenset({"driving", "cycling", "walking"})
VERIFICATION_ONLY_HOSTS = frozenset({"router.project-osrm.org"})
_RUNTIME_LOCK = threading.Lock()
_LAST_SUCCESS: float | None = None
_LAST_ERROR: str | None = None


class RoutingUnavailable(RuntimeError):
    """Raised when an approved routing endpoint cannot return bounded routing data."""


def _flag(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() == "true"


def _host_set(name: str) -> frozenset[str]:
    return frozenset(item.strip().casefold() for item in os.environ.get(name, "").split(",") if item.strip())


def _allowed_hosts() -> frozenset[str]:
    return _host_set("OAP_OSRM_ALLOWED_HOSTS")


def _owned_hosts() -> frozenset[str]:
    return _host_set("OAP_ROUTING_OWNED_HOSTS")


def _validated_base_url(value: object, *, require_owned: bool = False) -> str:
    raw = str(value or "").strip().rstrip("/")
    if not raw:
        return ""
    parsed = urlparse.urlparse(raw)
    host = str(parsed.hostname or "").casefold()
    if parsed.scheme != "https" or not host or parsed.username or parsed.password:
        return ""
    if parsed.query or parsed.fragment or host not in _allowed_hosts():
        return ""
    if require_owned and host not in _owned_hosts():
        return ""
    path = parsed.path.rstrip("/")
    return urlparse.urlunparse(("https", parsed.netloc, path, "", "", ""))


def _base_url() -> str:
    return _validated_base_url(os.environ.get("OAP_OSRM_BASE_URL", ""))


def configured() -> bool:
    return bool(_base_url())


def provider_tier() -> str:
    base = _base_url()
    if not base:
        return "unconfigured"
    host = str(urlparse.urlparse(base).hostname or "").casefold()
    return "verification_only" if host in VERIFICATION_ONLY_HOSTS else "production_candidate"


def provider_ownership() -> str:
    base = _base_url()
    if not base:
        return "unconfigured"
    host = str(urlparse.urlparse(base).hostname or "").casefold()
    if host in VERIFICATION_ONLY_HOSTS:
        return "verification_only"
    return "oap_owned" if host in _owned_hosts() else "external_candidate"


def production_approval_state() -> dict[str, bool]:
    return {
        "provider_approved": _flag("OAP_ROUTING_PRODUCTION_APPROVED"),
        "capacity_approved": _flag("OAP_ROUTING_CAPACITY_APPROVED"),
        "monitoring_approved": _flag("OAP_ROUTING_MONITORING_APPROVED"),
    }


def production_gate_approved() -> bool:
    gates = production_approval_state()
    return provider_tier() == "production_candidate" and all(gates.values())


def _runtime_state() -> tuple[float | None, str | None]:
    with _RUNTIME_LOCK:
        return _LAST_SUCCESS, _LAST_ERROR


def runtime_verified() -> bool:
    success, error = _runtime_state()
    return success is not None and error is None


def production_ready() -> bool:
    return production_gate_approved() and runtime_verified()


def _mark_error(error: str) -> None:
    with _RUNTIME_LOCK:
        global _LAST_ERROR
        _LAST_ERROR = error


def _mark_success() -> None:
    with _RUNTIME_LOCK:
        global _LAST_SUCCESS, _LAST_ERROR
        _LAST_SUCCESS = time.time(); _LAST_ERROR = None


def _coordinate(value: object, *, minimum: float, maximum: float, name: str) -> float:
    try:
        number = round(float(value), 6)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"invalid_{name}") from exc
    if not minimum <= number <= maximum:
        raise ValueError(f"invalid_{name}")
    return number


def _profile(value: object) -> str:
    profile = str(value or "driving").strip().casefold()
    if profile == "transit":
        profile = "driving"
    if profile not in ALLOWED_PROFILES:
        raise ValueError("invalid_route_profile")
    return profile


def _request_json(url: str, *, expected_host: str) -> dict[str, Any]:
    parsed = urlparse.urlparse(url)
    if parsed.scheme != "https" or parsed.hostname != expected_host:
        raise RoutingUnavailable("routing_endpoint_rejected")
    request = urlrequest.Request(url, headers={"Accept":"application/json","User-Agent":"ON-ANY-POSTCODE-Movement/1.0"})
    try:
        with urlrequest.urlopen(request, timeout=ROUTE_TIMEOUT_SECONDS) as response:
            final = urlparse.urlparse(response.geturl())
            if final.scheme != "https" or final.hostname != expected_host:
                _mark_error("routing_redirect_rejected"); raise RoutingUnavailable("routing_redirect_rejected")
            body = response.read(MAX_RESPONSE_BYTES + 1)
    except RoutingUnavailable:
        raise
    except (OSError, TimeoutError) as exc:
        _mark_error(type(exc).__name__); raise RoutingUnavailable("routing_provider_unavailable") from exc
    if len(body) > MAX_RESPONSE_BYTES:
        _mark_error("routing_response_too_large"); raise RoutingUnavailable("routing_response_too_large")
    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        _mark_error("invalid_routing_response"); raise RoutingUnavailable("invalid_routing_response") from exc
    if not isinstance(payload, dict):
        _mark_error("invalid_routing_response"); raise RoutingUnavailable("invalid_routing_response")
    return payload


def _request_bytes(url: str, *, expected_host: str, max_bytes: int) -> tuple[bytes, str]:
    parsed = urlparse.urlparse(url)
    if parsed.scheme != "https" or parsed.hostname != expected_host:
        raise RoutingUnavailable("routing_endpoint_rejected")
    request = urlrequest.Request(url, headers={"Accept":"application/x-protobuf","User-Agent":"ON-ANY-POSTCODE-Map/1.0"})
    try:
        with urlrequest.urlopen(request, timeout=ROUTE_TIMEOUT_SECONDS) as response:
            final = urlparse.urlparse(response.geturl())
            if final.scheme != "https" or final.hostname != expected_host:
                _mark_error("routing_redirect_rejected"); raise RoutingUnavailable("routing_redirect_rejected")
            body = response.read(max_bytes + 1)
            content_type = str(response.headers.get("Content-Type") or "application/x-protobuf").split(";", 1)[0].strip()
    except RoutingUnavailable:
        raise
    except (OSError, TimeoutError) as exc:
        _mark_error(type(exc).__name__); raise RoutingUnavailable("routing_provider_unavailable") from exc
    if len(body) > max_bytes:
        _mark_error("routing_tile_too_large"); raise RoutingUnavailable("routing_tile_too_large")
    if not body:
        raise RoutingUnavailable("routing_tile_empty")
    _mark_success()
    return body, content_type


def _route_payload(*, pickup_latitude: object, pickup_longitude: object, destination_latitude: object, destination_longitude: object, profile: object, geometry: bool, base_url: str | None = None) -> tuple[dict[str, Any], str]:
    base = base_url or _base_url()
    if not base:
        raise RoutingUnavailable("routing_provider_not_configured")
    parsed_base = urlparse.urlparse(base)
    expected_host = str(parsed_base.hostname)
    pickup_lat = _coordinate(pickup_latitude, minimum=-90, maximum=90, name="pickup_latitude")
    pickup_lon = _coordinate(pickup_longitude, minimum=-180, maximum=180, name="pickup_longitude")
    destination_lat = _coordinate(destination_latitude, minimum=-90, maximum=90, name="destination_latitude")
    destination_lon = _coordinate(destination_longitude, minimum=-180, maximum=180, name="destination_longitude")
    normalized_profile = _profile(profile)
    coordinates = f"{pickup_lon},{pickup_lat};{destination_lon},{destination_lat}"
    query_values = {"overview":"full" if geometry else "false","steps":"true" if geometry else "false","alternatives":"false"}
    if geometry:
        query_values["geometries"] = "geojson"
    url = f"{base}/route/v1/{normalized_profile}/{coordinates}?{urlparse.urlencode(query_values)}"
    payload = _request_json(url, expected_host=expected_host)
    if payload.get("code") != "Ok":
        _mark_error("route_not_found"); raise RoutingUnavailable("route_not_found")
    return payload, normalized_profile


def route(*, pickup_latitude: object, pickup_longitude: object, destination_latitude: object, destination_longitude: object, profile: object = "driving", verification_only: bool = False) -> dict[str, Any]:
    tier = provider_tier()
    if not verification_only:
        if tier == "verification_only":
            raise RoutingUnavailable("routing_provider_verification_only")
        if tier == "production_candidate" and not production_gate_approved():
            raise RoutingUnavailable("routing_provider_not_production_approved")
    payload, normalized_profile = _route_payload(pickup_latitude=pickup_latitude,pickup_longitude=pickup_longitude,destination_latitude=destination_latitude,destination_longitude=destination_longitude,profile=profile,geometry=False)
    routes = payload.get("routes")
    if not isinstance(routes, list) or not routes or not isinstance(routes[0], dict):
        _mark_error("invalid_routing_response"); raise RoutingUnavailable("invalid_routing_response")
    first = routes[0]
    try:
        distance_m = max(0.0, float(first["distance"])); duration_s = max(0.0, float(first["duration"]))
    except (KeyError, TypeError, ValueError) as exc:
        _mark_error("invalid_routing_response"); raise RoutingUnavailable("invalid_routing_response") from exc
    _mark_success()
    return {"distance_m":round(distance_m,1),"duration_s":round(duration_s,1),"profile":normalized_profile,"provider":CORE_NAME,"engine_contract":ENGINE_CONTRACT,"provider_ownership":provider_ownership(),"geometry_exposed":False,"dispatch_performed":False}


def _map_route_with_base(*, base: str, pickup_latitude: object, pickup_longitude: object, destination_latitude: object, destination_longitude: object, profile: object = "driving") -> dict[str, Any]:
    payload, normalized_profile = _route_payload(pickup_latitude=pickup_latitude,pickup_longitude=pickup_longitude,destination_latitude=destination_latitude,destination_longitude=destination_longitude,profile=profile,geometry=True,base_url=base)
    routes = payload.get("routes")
    if not isinstance(routes, list) or not routes or not isinstance(routes[0], dict):
        raise RoutingUnavailable("invalid_routing_response")
    first = routes[0]
    geometry = first.get("geometry")
    if not isinstance(geometry, dict) or geometry.get("type") != "LineString" or not isinstance(geometry.get("coordinates"), list):
        raise RoutingUnavailable("route_geometry_unavailable")
    coords = geometry["coordinates"][:5000]
    if len(coords) < 2:
        raise RoutingUnavailable("route_geometry_unavailable")
    legs = first.get("legs") if isinstance(first.get("legs"), list) else []
    steps: list[dict[str, Any]] = []
    for leg in legs:
        if not isinstance(leg, dict): continue
        for step in leg.get("steps", []) if isinstance(leg.get("steps"), list) else []:
            if not isinstance(step, dict): continue
            maneuver = step.get("maneuver") if isinstance(step.get("maneuver"), dict) else {}
            steps.append({"name":str(step.get("name") or "")[:120],"distance_m":round(float(step.get("distance") or 0),1),"duration_s":round(float(step.get("duration") or 0),1),"type":str(maneuver.get("type") or "")[:40],"modifier":str(maneuver.get("modifier") or "")[:40]})
            if len(steps) >= 100: break
        if len(steps) >= 100: break
    _mark_success()
    return {"distance_m":round(float(first.get("distance") or 0),1),"duration_s":round(float(first.get("duration") or 0),1),"profile":normalized_profile,"provider":CORE_NAME,"provider_ownership":"oap_owned","geometry":{"type":"LineString","coordinates":coords},"steps":steps,"geometry_exposed":True,"read_only":True,"dispatch_performed":False,"payment_performed":False}


def map_route_via_owned_endpoint(*, base_url: object, pickup_latitude: object, pickup_longitude: object, destination_latitude: object, destination_longitude: object, profile: object = "driving") -> dict[str, Any]:
    base = _validated_base_url(base_url, require_owned=True)
    if not base:
        raise RoutingUnavailable("routing_shard_endpoint_rejected")
    return _map_route_with_base(base=base,pickup_latitude=pickup_latitude,pickup_longitude=pickup_longitude,destination_latitude=destination_latitude,destination_longitude=destination_longitude,profile=profile)


def map_route(*, pickup_latitude: object, pickup_longitude: object, destination_latitude: object, destination_longitude: object, profile: object = "driving") -> dict[str, Any]:
    if provider_ownership() != "oap_owned":
        raise RoutingUnavailable("map_routing_requires_oap_owned_endpoint")
    base = _validated_base_url(os.environ.get("OAP_OSRM_BASE_URL", ""), require_owned=True)
    if not base:
        raise RoutingUnavailable("routing_provider_not_configured")
    return _map_route_with_base(base=base,pickup_latitude=pickup_latitude,pickup_longitude=pickup_longitude,destination_latitude=destination_latitude,destination_longitude=destination_longitude,profile=profile)


def road_tile(*, x: object, y: object, zoom: object, profile: object = "driving") -> tuple[bytes, str]:
    """Fetch one routable-road MVT tile from the current OAP-owned routing graph."""
    if provider_ownership() != "oap_owned":
        raise RoutingUnavailable("map_tiles_require_oap_owned_endpoint")
    try:
        tx = int(x); ty = int(y); z = int(zoom)
    except (TypeError, ValueError) as exc:
        raise ValueError("invalid_tile_coordinate") from exc
    if z < 12 or z > 20 or tx < 0 or ty < 0:
        raise ValueError("invalid_tile_coordinate")
    limit = 1 << z
    if tx >= limit or ty >= limit:
        raise ValueError("invalid_tile_coordinate")
    normalized_profile = _profile(profile)
    base = _validated_base_url(os.environ.get("OAP_OSRM_BASE_URL", ""), require_owned=True)
    if not base:
        raise RoutingUnavailable("routing_provider_not_configured")
    expected_host = str(urlparse.urlparse(base).hostname)
    url = f"{base}/tile/v1/{normalized_profile}/tile({tx},{ty},{z}).mvt"
    return _request_bytes(url, expected_host=expected_host, max_bytes=MAX_TILE_BYTES)


def startup_probe() -> dict[str, Any]:
    if not _flag("OAP_ROUTING_STARTUP_PROBE") or not configured():
        return status()
    if provider_ownership() == "oap_owned":
        try:
            result = map_route(
                pickup_latitude=51.4036,
                pickup_longitude=-0.1687,
                destination_latitude=51.5079,
                destination_longitude=-0.0877,
                profile="driving",
            )
            canonical_geometry = json.dumps(
                result["geometry"], sort_keys=True, separators=(",", ":")
            )
            print(
                json.dumps(
                    {
                        "event": "oap_routing_startup_geometry_proof",
                        "provider_ownership": "oap_owned",
                        "route_geometry_proven": True,
                        "distance_m": result["distance_m"],
                        "duration_s": result["duration_s"],
                        "geometry_sha256": hashlib.sha256(
                            canonical_geometry.encode("utf-8")
                        ).hexdigest(),
                        "dispatch_performed": False,
                        "payment_performed": False,
                        "tracking_performed": False,
                    },
                    sort_keys=True,
                ),
                flush=True,
            )
        except (RoutingUnavailable, ValueError, KeyError, TypeError):
            print(
                json.dumps(
                    {
                        "event": "oap_routing_startup_geometry_proof",
                        "provider_ownership": provider_ownership(),
                        "route_geometry_proven": False,
                        "last_error": _runtime_state()[1],
                        "dispatch_performed": False,
                        "payment_performed": False,
                        "tracking_performed": False,
                    },
                    sort_keys=True,
                ),
                flush=True,
            )
    else:
        try:
            route(
                pickup_latitude=51.401,
                pickup_longitude=-0.166,
                destination_latitude=51.462,
                destination_longitude=-0.115,
                profile="driving",
                verification_only=True,
            )
        except (RoutingUnavailable, ValueError):
            pass
    return status()


def status() -> dict[str, Any]:
    success, error = _runtime_state(); approvals = production_approval_state(); ownership = provider_ownership()
    return {"component":CORE_NAME,"engine_contract":ENGINE_CONTRACT,"configured":configured(),"runtime_verified":success is not None and error is None,"provider_tier":provider_tier(),"provider_ownership":ownership,"oap_owned_endpoint":ownership=="oap_owned","production_provider_approved":approvals["provider_approved"],"production_capacity_approved":approvals["capacity_approved"],"production_monitoring_approved":approvals["monitoring_approved"],"production_gate_approved":production_gate_approved(),"production_ready":production_ready(),"startup_probe_enabled":_flag("OAP_ROUTING_STARTUP_PROBE"),"last_success_epoch":int(success) if success is not None else None,"last_error":error,"timeout_seconds":ROUTE_TIMEOUT_SECONDS,"geometry_exposed":ownership=="oap_owned","road_vector_tiles":ownership=="oap_owned","road_vector_tile_min_zoom":12,"mutation_enabled":False,"dispatch_enabled":False}
