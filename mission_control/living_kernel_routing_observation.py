"""Read-only OSRM observation for the existing Living Kernel evidence path.

This module never starts services, retries deployments or grants authority.
Its state describes one actual probe, not production certification.
"""
from __future__ import annotations

import json
import time
from datetime import UTC, datetime
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

_ROUTE = "http://127.0.0.1:10000/route/v1/driving/-0.1687,51.4036;-0.0877,51.5079?overview=full&geometries=geojson"
_MAX_BYTES = 262144


def observe_local_routing(*, timeout: float = 3.0) -> dict[str, object]:
    """Return bounded, factual loopback evidence; fail closed on missing service."""
    observed_at = datetime.now(UTC).isoformat()
    result: dict[str, object] = {
        "component": "osrm_routing",
        "observed_at": observed_at,
        "scope": "local_loopback_only",
        "state": "BLOCKED",
        "verified": False,
        "public_https_verified": False,
        "production_green_gate_passed": False,
        "authority": "observation_only",
    }
    if not 0 < timeout <= 10:
        raise ValueError("timeout must be in (0, 10]")
    start = time.monotonic()
    try:
        with urlopen(_ROUTE, timeout=timeout) as response:
            if response.status != 200:
                result["reason"] = "unexpected_http_status"
                return result
            raw = response.read(_MAX_BYTES + 1)
            if len(raw) > _MAX_BYTES:
                result["reason"] = "response_too_large"
                return result
        payload = json.loads(raw)
        routes = payload.get("routes")
        route = routes[0] if isinstance(routes, list) and routes else None
        geometry = route.get("geometry") if isinstance(route, dict) else None
        coordinates = geometry.get("coordinates") if isinstance(geometry, dict) else None
        valid = (
            payload.get("code") == "Ok"
            and isinstance(route, dict)
            and type(route.get("distance")) in (float, int)
            and route["distance"] > 0
            and type(route.get("duration")) in (float, int)
            and route["duration"] > 0
            and isinstance(geometry, dict)
            and geometry.get("type") == "LineString"
            and isinstance(coordinates, list)
            and len(coordinates) >= 2
            and all(
                isinstance(p, list) and len(p) >= 2
                and all(type(v) in (float, int) and -180 <= v <= 180 for v in p[:2])
                for p in coordinates
            )
        )
        if not valid:
            result.update(state="DEGRADED", reason="invalid_route_geometry")
            return result
        result.update(
            state="LOCAL_ROUTE_VERIFIED",
            verified=True,
            latency_ms=round((time.monotonic() - start) * 1000, 2),
            distance_m=route["distance"],
            duration_s=route["duration"],
            geometry_points=len(coordinates),
        )
    except (HTTPError, URLError, TimeoutError, OSError, ValueError, TypeError, KeyError, json.JSONDecodeError):
        result["reason"] = "route_probe_unavailable_or_invalid"
    return result
