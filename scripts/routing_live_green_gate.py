#!/usr/bin/env python3
from __future__ import annotations

import concurrent.futures
import json
import statistics
import time
from urllib import error, parse, request

BASE = "https://oap-routing.onrender.com"
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
    return f"{BASE}/route/v1/driving/{coords}?{query}"


def wait_until_ready() -> dict[str, object]:
    started = time.perf_counter()
    last_failure = "not_started"
    for attempt in range(1, WARMUP_ATTEMPTS + 1):
        req = request.Request(
            _route_url(0),
            headers={"Accept": "application/json", "User-Agent": "OAP-Green-Gate-Warmup/1.0"},
        )
        try:
            with request.urlopen(req, timeout=WARMUP_TIMEOUT_SECONDS) as response:
                payload = json.loads(response.read().decode("utf-8"))
                routes = payload.get("routes") if isinstance(payload, dict) else None
                first = routes[0] if isinstance(routes, list) and routes else {}
                geometry = first.get("geometry") if isinstance(first, dict) else {}
                coordinates = geometry.get("coordinates") if isinstance(geometry, dict) else None
                if (
                    int(response.status) == 200
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
        with request.urlopen(req, timeout=TIMEOUT_SECONDS) as response:
            status = int(response.status)
            payload = json.loads(response.read().decode("utf-8"))
            if not isinstance(payload, dict):
                raise ValueError("routing response must be a JSON object")
    except (TimeoutError, error.URLError, OSError, ValueError, UnicodeError) as exc:
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
