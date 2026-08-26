"""Bounded, read-only routing adapter for OAP Movement.

The adapter is deliberately provider-shaped rather than vendor-owned. A deployment
must explicitly configure an HTTPS OSRM-compatible endpoint and explicitly allow
its hostname. Status reads never probe the network. Successful route requests
record coarse runtime evidence only; no route request dispatches a person,
vehicle, courier or payment.

Known public demonstration endpoints may be used for bounded verification, but
are never treated as production-ready routing providers and are blocked from
normal Movement route requests.
"""
from __future__ import annotations

import json
import os
import threading
import time
from typing import Any
from urllib import parse as urlparse
from urllib import request as urlrequest

MAX_RESPONSE_BYTES = 128 * 1024
ROUTE_TIMEOUT_SECONDS = 6
ALLOWED_PROFILES = frozenset({"driving", "cycling", "walking"})
VERIFICATION_ONLY_HOSTS = frozenset({"router.project-osrm.org"})
_RUNTIME_LOCK = threading.Lock()
_LAST_SUCCESS: float | None = None
_LAST_ERROR: str | None = None


class RoutingUnavailable(RuntimeError):
    """Raised when an approved routing endpoint cannot return a bounded route."""


def _allowed_hosts() -> frozenset[str]:
    return frozenset(
        item.strip().casefold()
        for item in os.environ.get("OAP_OSRM_ALLOWED_HOSTS", "").split(",")
        if item.strip()
    )


def _base_url() -> str:
    value = os.environ.get("OAP_OSRM_BASE_URL", "").strip().rstrip("/")
    if not value:
        return ""
    parsed = urlparse.urlparse(value)
    host = str(parsed.hostname or "").casefold()
    if parsed.scheme != "https" or not host or parsed.username or parsed.password:
        return ""
    if parsed.query or parsed.fragment:
        return ""
    if host not in _allowed_hosts():
        return ""
    path = parsed.path.rstrip("/")
    return urlparse.urlunparse(("https", parsed.netloc, path, "", "", ""))


def configured() -> bool:
    """Return whether a routing endpoint passes local configuration validation."""

    return bool(_base_url())


def provider_tier() -> str:
    """Classify the configured endpoint without claiming contractual readiness."""

    base = _base_url()
    if not base:
        return "unconfigured"
    host = str(urlparse.urlparse(base).hostname or "").casefold()
    if host in VERIFICATION_ONLY_HOSTS:
        return "verification_only"
    return "production_candidate"


def production_ready() -> bool:
    """Require both a non-demo endpoint and explicit production approval."""

    return (
        provider_tier() == "production_candidate"
        and os.environ.get("OAP_ROUTING_PRODUCTION_APPROVED", "").strip().lower()
        == "true"
    )


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
    if profile not in ALLOWED_PROFILES:
        raise ValueError("invalid_route_profile")
    return profile


def _request_json(url: str, *, expected_host: str) -> dict[str, Any]:
    parsed = urlparse.urlparse(url)
    if parsed.scheme != "https" or parsed.hostname != expected_host:
        raise RoutingUnavailable("routing_endpoint_rejected")
    request = urlrequest.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "ON-ANY-POSTCODE-Movement/1.0",
        },
    )
    try:
        with urlrequest.urlopen(request, timeout=ROUTE_TIMEOUT_SECONDS) as response:
            final = urlparse.urlparse(response.geturl())
            if final.scheme != "https" or final.hostname != expected_host:
                raise RoutingUnavailable("routing_redirect_rejected")
            body = response.read(MAX_RESPONSE_BYTES + 1)
    except (OSError, TimeoutError) as exc:
        with _RUNTIME_LOCK:
            global _LAST_ERROR
            _LAST_ERROR = type(exc).__name__
        raise RoutingUnavailable("routing_provider_unavailable") from exc
    if len(body) > MAX_RESPONSE_BYTES:
        raise RoutingUnavailable("routing_response_too_large")
    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RoutingUnavailable("invalid_routing_response") from exc
    if not isinstance(payload, dict):
        raise RoutingUnavailable("invalid_routing_response")
    return payload


def route(
    *,
    pickup_latitude: object,
    pickup_longitude: object,
    destination_latitude: object,
    destination_longitude: object,
    profile: object = "driving",
    verification_only: bool = False,
) -> dict[str, Any]:
    """Calculate distance and ETA without returning precise route geometry."""

    base = _base_url()
    if not base:
        raise RoutingUnavailable("routing_provider_not_configured")
    if provider_tier() == "verification_only" and not verification_only:
        raise RoutingUnavailable("routing_provider_verification_only")
    parsed_base = urlparse.urlparse(base)
    expected_host = str(parsed_base.hostname)
    pickup_lat = _coordinate(
        pickup_latitude, minimum=-90, maximum=90, name="pickup_latitude"
    )
    pickup_lon = _coordinate(
        pickup_longitude, minimum=-180, maximum=180, name="pickup_longitude"
    )
    destination_lat = _coordinate(
        destination_latitude,
        minimum=-90,
        maximum=90,
        name="destination_latitude",
    )
    destination_lon = _coordinate(
        destination_longitude,
        minimum=-180,
        maximum=180,
        name="destination_longitude",
    )
    normalized_profile = _profile(profile)
    coordinates = (
        f"{pickup_lon},{pickup_lat};{destination_lon},{destination_lat}"
    )
    query = urlparse.urlencode(
        {
            "overview": "false",
            "steps": "false",
            "alternatives": "false",
        }
    )
    url = f"{base}/route/v1/{normalized_profile}/{coordinates}?{query}"
    payload = _request_json(url, expected_host=expected_host)
    if payload.get("code") != "Ok":
        with _RUNTIME_LOCK:
            global _LAST_ERROR
            _LAST_ERROR = "route_not_found"
        raise RoutingUnavailable("route_not_found")
    routes = payload.get("routes")
    if not isinstance(routes, list) or not routes or not isinstance(routes[0], dict):
        raise RoutingUnavailable("invalid_routing_response")
    first = routes[0]
    try:
        distance_m = max(0.0, float(first["distance"]))
        duration_s = max(0.0, float(first["duration"]))
    except (KeyError, TypeError, ValueError) as exc:
        raise RoutingUnavailable("invalid_routing_response") from exc
    with _RUNTIME_LOCK:
        global _LAST_SUCCESS
        _LAST_SUCCESS = time.time()
        _LAST_ERROR = None
    return {
        "distance_m": round(distance_m, 1),
        "duration_s": round(duration_s, 1),
        "profile": normalized_profile,
        "provider": "OSRM-compatible routing",
        "geometry_exposed": False,
        "dispatch_performed": False,
    }


def startup_probe() -> dict[str, Any]:
    """Optionally verify outbound routing once at app startup using fixed public coordinates."""

    if (
        os.environ.get("OAP_ROUTING_STARTUP_PROBE", "").strip().lower()
        != "true"
    ):
        return status()
    if not configured():
        return status()
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
    """Return coarse local/runtime evidence without making a network request."""

    with _RUNTIME_LOCK:
        success = _LAST_SUCCESS
        error = _LAST_ERROR
    return {
        "configured": configured(),
        "runtime_verified": success is not None,
        "provider_tier": provider_tier(),
        "production_ready": production_ready(),
        "startup_probe_enabled": (
            os.environ.get("OAP_ROUTING_STARTUP_PROBE", "").strip().lower()
            == "true"
        ),
        "last_success_epoch": int(success) if success is not None else None,
        "last_error": error,
        "timeout_seconds": ROUTE_TIMEOUT_SECONDS,
        "geometry_exposed": False,
        "mutation_enabled": False,
    }
