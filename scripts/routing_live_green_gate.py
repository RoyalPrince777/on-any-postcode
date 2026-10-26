#!/usr/bin/env python3
from __future__ import annotations

import concurrent.futures
import ipaddress
import json
import os
import re
import socket
import ssl
import statistics
import time
from urllib import error, parse, request

# Reuse the existing Movement/Map owned-endpoint configuration contract.
# Never select a hosting vendor, public/demo route engine, or silent fallback.
_ROUTING_BASE_VAR = "OAP_OSRM_BASE_URL"
_HOST_PATTERN = re.compile(r"^[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?$")


class RoutingOriginRejected(ValueError):
    """Missing or non-approved OAP-controlled routing endpoint."""


def _configured_base() -> str:
    """Require explicit HTTPS OAP-owned and allowlisted host; no runtime claim."""
    raw = os.environ.get(_ROUTING_BASE_VAR, "").strip()
    if not raw:
        raise RoutingOriginRejected("routing_origin_not_configured")
    try:
        parsed = parse.urlsplit(raw)
        host = str(parsed.hostname or "").casefold()
        port = parsed.port
    except ValueError as exc:
        raise RoutingOriginRejected("routing_origin_rejected") from exc
    if (parsed.scheme != "https" or not host or port is not None
            or parsed.username is not None or parsed.password is not None
            or parsed.path not in ("", "/") or parsed.query or parsed.fragment):
        raise RoutingOriginRejected("routing_origin_rejected")
    if (len(host) > 253 or ".." in host or not _HOST_PATTERN.fullmatch(host)
            or any(len(label) > 63 for label in host.split("."))):
        raise RoutingOriginRejected("routing_origin_rejected")
    try:
        ipaddress.ip_address(host)
    except ValueError:
        pass
    else:
        raise RoutingOriginRejected("routing_origin_rejected")
    if (host in {"localhost", "onrender.com"}
            or host.endswith(".onrender.com") or "." not in host):
        raise RoutingOriginRejected("routing_origin_rejected")

    allowed = {
        name.strip().casefold()
        for name in os.environ.get("OAP_OSRM_ALLOWED_HOSTS", "").split(",")
        if name.strip()
    }
    owned = {
        name.strip().casefold()
        for name in os.environ.get("OAP_ROUTING_OWNED_HOSTS", "").split(",")
        if name.strip()
    }
    if host not in allowed or host not in owned:
        raise RoutingOriginRejected("routing_origin_not_allowlisted_and_owned")
    return f"https://{host}"
ROUTES = (
    (-0.1687, 51.4036, -0.0877, 51.5079, "mitcham_london_bridge"),
    (-0.1687, 51.4036, -0.1238, 51.5308, "mitcham_kings_cross"),
)
TOTAL_REQUESTS = 20
WORKERS = 4
TIMEOUT_SECONDS = 10
P95_LIMIT_SECONDS = 6.0
WARMUP_ATTEMPTS = 6
WARMUP_TIMEOUT_SECONDS = 10
WARMUP_SLEEP_SECONDS = 2.0
MAX_RESPONSE_BYTES = 512 * 1024


class _RejectRedirects(request.HTTPRedirectHandler):
    """No redirected routing responses; the destination must be approved."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise RoutingOriginRejected("routing_redirect_rejected")


_OPENER = request.build_opener(_RejectRedirects)


def _open_owned_json(req: request.Request, timeout: int) -> tuple[int, dict[str, object]]:
    """Require same approved HTTPS origin and bounded JSON, without redirects."""
    approved = _configured_base()
    if not req.full_url.startswith(f"{approved}/route/v1/driving/"):
        raise RoutingOriginRejected("routing_origin_rejected")
    with _OPENER.open(req, timeout=timeout) as response:
        actual = parse.urlsplit(response.geturl())
        if actual.scheme != "https" or actual.netloc.casefold() != parse.urlsplit(approved).netloc:
            raise RoutingOriginRejected("routing_redirect_rejected")
        raw = response.read(MAX_RESPONSE_BYTES + 1)
        if len(raw) > MAX_RESPONSE_BYTES:
            raise ValueError("routing_response_too_large")
        payload = json.loads(raw.decode("utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("routing_response_not_object")
        return int(response.status), payload



def _failure_reason(exc: BaseException) -> str:
    """Stable failure codes, never print headers, response bodies or URLs."""
    if isinstance(exc, error.HTTPError):
        code = int(exc.code)
        return f"http_{code}" if 100 <= code <= 599 else "http_error"
    if isinstance(exc, error.URLError):
        reason = exc.reason
        if isinstance(reason, socket.gaierror):
            return "dns_resolution_failed"
        if isinstance(reason, ssl.SSLError):
            return "tls_failure"
        if isinstance(reason, (TimeoutError, socket.timeout)):
            return "timeout"
        if isinstance(reason, ConnectionRefusedError):
            return "connection_refused"
        if isinstance(reason, ConnectionResetError):
            return "connection_reset"
        return "transport_error"
    if isinstance(exc, RoutingOriginRejected):
        return "routing_origin_rejected"
    if isinstance(exc, (TimeoutError, socket.timeout)):
        return "timeout"
    if isinstance(exc, UnicodeError):
        return "invalid_encoding"
    if isinstance(exc, ValueError):
        return "invalid_json_or_payload"
    if isinstance(exc, OSError):
        return "transport_error"
    return "unknown"


def _route_url(index: int) -> str:
    from_lon, from_lat, to_lon, to_lat, _route_id = ROUTES[index % len(ROUTES)]
    coords = f"{from_lon},{from_lat};{to_lon},{to_lat}"
    query = parse.urlencode(
        {
            "overview": "full",
            "steps": "true",
            "alternatives": "false",
            "geometries": "geojson",
        }
    )
    return f"{_configured_base()}/route/v1/driving/{coords}?{query}"


def wait_until_ready() -> dict[str, object]:
    started = time.perf_counter()
    last_failure = "not_started"
    last_reason = "not_started"
    for attempt in range(1, WARMUP_ATTEMPTS + 1):
        req = request.Request(
            _route_url(0),
            headers={"Accept": "application/json", "User-Agent": "OAP-Green-Gate-Warmup/1.0"},
        )
        try:
            status, payload = _open_owned_json(req, WARMUP_TIMEOUT_SECONDS)
            routes = payload.get("routes")
            first = routes[0] if isinstance(routes, list) and routes else {}
            geometry = first.get("geometry") if isinstance(first, dict) else {}
            coordinates = geometry.get("coordinates") if isinstance(geometry, dict) else None
            if (
                status == 200
                and payload.get("code") == "Ok"
                and float(first.get("distance") or 0) > 0
                and float(first.get("duration") or 0) > 0
                and geometry.get("type") == "LineString"
                and isinstance(coordinates, list)
                and len(coordinates) >= 2
            ):
                return {
                    "ready": True,
                    "attempts": attempt,
                    "elapsed_s": time.perf_counter() - started,
                }
            last_failure = "invalid_response"
            last_reason = "route_payload_invalid"
        except (TimeoutError, error.URLError, OSError, ValueError, UnicodeError, RoutingOriginRejected) as exc:
            last_reason = _failure_reason(exc)
            last_failure = "timeout" if last_reason == "timeout" else "request_or_response_error"
        if attempt < WARMUP_ATTEMPTS:
            time.sleep(WARMUP_SLEEP_SECONDS)
    return {
        "ready": False,
        "attempts": WARMUP_ATTEMPTS,
        "elapsed_s": time.perf_counter() - started,
        "failure_type": last_failure,
        "failure_reason": last_reason,
    }


def run_one(index: int) -> dict[str, object]:
    _from_lon, _from_lat, _to_lon, _to_lat, route_id = ROUTES[index % len(ROUTES)]
    url = _route_url(index)
    req = request.Request(
        url,
        headers={"Accept": "application/json", "User-Agent": "OAP-Green-Gate/1.0"},
    )
    started = time.perf_counter()
    try:
        status, payload = _open_owned_json(req, TIMEOUT_SECONDS)
    except (TimeoutError, error.URLError, OSError, ValueError, UnicodeError, RoutingOriginRejected) as exc:
        elapsed = time.perf_counter() - started
        return {
            "route_id": route_id,
            "ok": False,
            "elapsed_s": elapsed,
            "failure_type": (
                "timeout" if _failure_reason(exc) == "timeout" else "request_or_response_error"
            ),
            "failure_reason": _failure_reason(exc),
            "distance_m": 0.0,
            "duration_s": 0.0,
        }
    elapsed = time.perf_counter() - started
    routes = payload.get("routes")
    first = routes[0] if isinstance(routes, list) and routes else {}
    geometry = first.get("geometry") if isinstance(first, dict) else {}
    coordinates = geometry.get("coordinates") if isinstance(geometry, dict) else None
    ok = (
        status == 200
        and payload.get("code") == "Ok"
        and float(first.get("distance") or 0) > 0
        and float(first.get("duration") or 0) > 0
        and geometry.get("type") == "LineString"
        and isinstance(coordinates, list)
        and len(coordinates) >= 2
    )
    return {
        "route_id": route_id,
        "ok": ok,
        "elapsed_s": elapsed,
        "distance_m": round(float(first.get("distance") or 0), 1),
        "duration_s": round(float(first.get("duration") or 0), 1),
    }


def main() -> None:
    try:
        _configured_base()
    except RoutingOriginRejected as exc:
        print(json.dumps({
            "event": "oap_routing_bounded_external_warmup",
            "ready": False,
            "attempts": 0,
            "failure_type": "configuration_blocked",
            "failure_reason": str(exc),
            "dispatch_performed": False,
            "payment_performed": False,
            "tracking_performed": False,
        }, sort_keys=True), flush=True)
        raise SystemExit("OAP-controlled HTTPS routing host not configured or approved") from exc
    warmup = wait_until_ready()
    print(
        json.dumps(
            {
                "event": "oap_routing_bounded_external_warmup",
                "ready": bool(warmup.get("ready")),
                "attempts": int(warmup.get("attempts") or 0),
                "elapsed_ms": round(float(warmup.get("elapsed_s") or 0) * 1000, 1),
                "failure_type": warmup.get("failure_type"),
                "failure_reason": warmup.get("failure_reason"),
                "dispatch_performed": False,
                "payment_performed": False,
                "tracking_performed": False,
            },
            sort_keys=True,
        )
    )
    if not warmup.get("ready"):
        raise SystemExit("live routing warmup did not become ready")

    with concurrent.futures.ThreadPoolExecutor(max_workers=WORKERS) as pool:
        results = list(pool.map(run_one, range(TOTAL_REQUESTS)))

    latencies = sorted(float(item["elapsed_s"]) for item in results)
    p95_index = max(0, min(len(latencies) - 1, int(0.95 * len(latencies)) - 1))
    p95 = latencies[p95_index]
    successes = sum(1 for item in results if item["ok"])
    timed_out = sum(1 for item in results if item.get("failure_type") == "timeout")
    failure_reasons = sorted({
        str(item.get("failure_reason"))
        for item in results if item.get("failure_reason")
    })
    receipt = {
        "event": "oap_routing_bounded_external_probe",
        "requests": TOTAL_REQUESTS,
        "workers": WORKERS,
        "successes": successes,
        "failures": TOTAL_REQUESTS - successes,
        "timeouts": timed_out,
        "failure_reasons": failure_reasons,
        "success_rate": round(successes / TOTAL_REQUESTS, 3),
        "p50_ms": round(statistics.median(latencies) * 1000, 1),
        "p95_ms": round(p95 * 1000, 1),
        "max_ms": round(max(latencies) * 1000, 1),
        "geometry_proven": all(bool(item["ok"]) for item in results),
        "bounded_capacity_proven": successes == TOTAL_REQUESTS and p95 <= P95_LIMIT_SECONDS,
        "dispatch_performed": False,
        "payment_performed": False,
        "tracking_performed": False,
    }
    print(json.dumps(receipt, sort_keys=True))
    if successes != TOTAL_REQUESTS:
        raise SystemExit("live routing probe had failed requests")
    if p95 > P95_LIMIT_SECONDS:
        raise SystemExit(f"live routing probe p95 exceeded {P95_LIMIT_SECONDS}s")


if __name__ == "__main__":
    main()
