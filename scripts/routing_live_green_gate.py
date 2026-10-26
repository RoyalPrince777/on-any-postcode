from __future__ import annotations

import concurrent.futures
import json
import math
import os
import statistics
import time
from urllib import error, parse, request


# The operational proof requires an explicit OAP-controlled HTTPS origin.
# URL validation does not independently attest infrastructure ownership.
def _https_origin(value: str) -> str:
    """Reject non-origin and ambiguous URL forms before issuing network requests."""
    message = "OAP_ROUTING_BASE_URL must be a valid HTTPS origin without credentials, path, query or fragment"
    if not value or value != value.strip() or any(ord(ch) <= 32 or ord(ch) == 127 for ch in value):
        raise ValueError(message)
    # Disallow ambiguous authorities, encoded delimiters and backslash normalization.
    if "\\" in value or "%" in value:
        raise ValueError(message)
    try:
        parsed = parse.urlsplit(value)
        port = parsed.port  # Validate numeric/range of an optional port.
    except ValueError as exc:
        raise ValueError(message) from exc
    if (
        parsed.scheme != "https"
        or not parsed.netloc
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path not in ("", "/")
        or parsed.query
        or parsed.fragment
        or "?" in value
        or "#" in value
        or "@" in parsed.netloc
        or port not in (None, 443)
        or (parsed.netloc.endswith(":") and port is None)
    ):
        raise ValueError(message)
    hostname = parsed.hostname.lower().rstrip(".")
    if hostname == "onrender.com" or hostname.endswith(".onrender.com"):
        raise ValueError("Render routing endpoints are not accepted for the OAP-hosted Green Gate")
    return value.rstrip("/")


def routing_base() -> str:
    value = os.environ.get("OAP_ROUTING_BASE_URL", "")
    if not value:
        raise ValueError("OAP_ROUTING_BASE_URL is required for the live routing gate")
    return _https_origin(value)


# Never let a live proof silently follow a redirect to another provider,
# an HTTP destination, or an unrelated host. Verify the configured origin itself.
class _RejectRedirects(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise error.HTTPError(req.full_url, code, "routing probe rejects redirects", headers, fp)


_OPENER = request.build_opener(_RejectRedirects)


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
    return f"{routing_base()}/route/v1/driving/{coords}?{query}"


def _route_metrics(payload: object, status: int) -> tuple[float, float] | None:
    """Validate finite route metrics and actual GeoJSON coordinate pairs."""
    try:
        if status != 200 or not isinstance(payload, dict) or payload.get("code") != "Ok":
            return None
        first = payload["routes"][0]
        values = (first["distance"], first["duration"])
        if any(type(value) not in (int, float) or not math.isfinite(value) or value <= 0 for value in values):
            return None
        geometry = first["geometry"]
        coordinates = geometry["coordinates"]
        if geometry.get("type") != "LineString" or not isinstance(coordinates, list) or len(coordinates) < 2:
            return None
        for point in coordinates:
            if not isinstance(point, list) or len(point) != 2:
                return None
            if any(type(value) not in (int, float) or not math.isfinite(value) for value in point):
                return None
            if not (-180 <= point[0] <= 180 and -90 <= point[1] <= 90):
                return None
        if all(point == coordinates[0] for point in coordinates):
            return None
        return float(values[0]), float(values[1])
    except (KeyError, IndexError, TypeError, ValueError, OverflowError):
        return None


def wait_until_ready() -> dict[str, object]:
    started = time.perf_counter()
    last_failure = "not_started"
    for attempt in range(1, WARMUP_ATTEMPTS + 1):
        req = request.Request(
            _route_url(0),
            headers={"Accept": "application/json", "User-Agent": "OAP-Green-Gate-Warmup/1.0"},
        )
        try:
            with _OPENER.open(req, timeout=WARMUP_TIMEOUT_SECONDS) as response:
                payload = json.loads(response.read().decode("utf-8"))
                if _route_metrics(payload, int(response.status)) is not None:
                    return {
                        "ready": True,
                        "attempts": attempt,
                        "elapsed_s": time.perf_counter() - started,
                    }
                last_failure = "invalid_response"
        except (TimeoutError, error.URLError, OSError, ValueError, UnicodeError) as exc:
            last_failure = "timeout" if isinstance(exc, TimeoutError) else "request_or_response_error"
        if attempt < WARMUP_ATTEMPTS:
            time.sleep(WARMUP_SLEEP_SECONDS)
    return {
        "ready": False,
        "attempts": WARMUP_ATTEMPTS,
        "elapsed_s": time.perf_counter() - started,
        "failure_type": last_failure,
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
        with _OPENER.open(req, timeout=TIMEOUT_SECONDS) as response:
            status = int(response.status)
            payload = json.loads(response.read().decode("utf-8"))
            if not isinstance(payload, dict):
                raise TypeError("routing response must be a JSON object")
    except (TimeoutError, error.URLError, OSError, ValueError, TypeError, UnicodeError) as exc:
        elapsed = time.perf_counter() - started
        return {
            "route_id": route_id,
            "ok": False,
            "elapsed_s": elapsed,
            "failure_type": "timeout" if isinstance(exc, TimeoutError) else "request_or_response_error",
            "distance_m": 0.0,
            "duration_s": 0.0,
        }
    elapsed = time.perf_counter() - started
    metrics = _route_metrics(payload, status)
    return {
        "route_id": route_id,
        "ok": metrics is not None,
        "elapsed_s": elapsed,
        "distance_m": round(metrics[0], 1) if metrics is not None else 0.0,
        "duration_s": round(metrics[1], 1) if metrics is not None else 0.0,
    }


def main() -> None:
    try:
        routing_base()
    except ValueError as exc:
        print(json.dumps({
            "event": "oap_routing_configuration", "ready": False,
            "failure_type": "invalid_or_missing_origin",
            "dispatch_performed": False, "payment_performed": False,
            "tracking_performed": False,
        }, sort_keys=True))
        raise SystemExit(str(exc)) from None
    warmup = wait_until_ready()
    print(
        json.dumps(
            {
                "event": "oap_routing_bounded_external_warmup",
                "ready": bool(warmup.get("ready")),
                "attempts": int(warmup.get("attempts") or 0),
                "elapsed_ms": round(float(warmup.get("elapsed_s") or 0) * 1000, 1),
                "failure_type": warmup.get("failure_type"),
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
    receipt = {
        "event": "oap_routing_bounded_external_probe",
        "requests": TOTAL_REQUESTS,
        "workers": WORKERS,
        "successes": successes,
        "failures": TOTAL_REQUESTS - successes,
        "timeouts": timed_out,
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
