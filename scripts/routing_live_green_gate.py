#!/usr/bin/env python3
from __future__ import annotations

import concurrent.futures
import json
import statistics
import time
from urllib import parse, request

BASE = "https://oap-routing.onrender.com"
APP_BASE = "https://on-any-postcode.onrender.com"
ROUTES = (
    (-0.1687, 51.4036, -0.0877, 51.5079, "mitcham_london_bridge"),
    (-0.1687, 51.4036, -0.1238, 51.5308, "mitcham_kings_cross"),
)
TOTAL_REQUESTS = 20
WORKERS = 4
TIMEOUT_SECONDS = 10
P95_LIMIT_SECONDS = 6.0


def run_one(index: int) -> dict[str, object]:
    from_lon, from_lat, to_lon, to_lat, route_id = ROUTES[index % len(ROUTES)]
    coords = f"{from_lon},{from_lat};{to_lon},{to_lat}"
    query = parse.urlencode(
        {
            "overview": "full",
            "steps": "true",
            "alternatives": "false",
            "geometries": "geojson",
        }
    )
    url = f"{BASE}/route/v1/driving/{coords}?{query}"
    req = request.Request(
        url,
        headers={"Accept": "application/json", "User-Agent": "OAP-Green-Gate/1.0"},
    )
    started = time.perf_counter()
    with request.urlopen(req, timeout=TIMEOUT_SECONDS) as response:
        status = int(response.status)
        payload = json.loads(response.read().decode("utf-8"))
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


def run_app_integration(origin: str, destination: str) -> dict[str, object]:
    query = parse.urlencode({"from": origin, "to": destination, "profile": "driving"})
    url = f"{APP_BASE}/map-intelligence/route?{query}"
    req = request.Request(
        url,
        headers={"Accept": "application/json", "User-Agent": "OAP-Green-Gate-App/1.0"},
    )
    started = time.perf_counter()
    with request.urlopen(req, timeout=TIMEOUT_SECONDS) as response:
        status = int(response.status)
        payload = json.loads(response.read().decode("utf-8"))
    elapsed = time.perf_counter() - started
    route = payload.get("route") if isinstance(payload, dict) else {}
    geometry = route.get("geometry") if isinstance(route, dict) else {}
    coordinates = geometry.get("coordinates") if isinstance(geometry, dict) else None
    ok = (
        status == 200
        and route.get("provider_ownership") == "oap_owned"
        and float(route.get("distance_m") or 0) > 0
        and float(route.get("duration_s") or 0) > 0
        and geometry.get("type") == "LineString"
        and isinstance(coordinates, list)
        and len(coordinates) >= 2
        and payload.get("operational_dispatch") is False
        and payload.get("payment_capture") is False
        and payload.get("hidden_tracking") is False
    )
    return {
        "ok": ok,
        "elapsed_s": elapsed,
        "distance_m": round(float(route.get("distance_m") or 0), 1),
        "duration_s": round(float(route.get("duration_s") or 0), 1),
    }


def main() -> None:
    with concurrent.futures.ThreadPoolExecutor(max_workers=WORKERS) as pool:
        results = list(pool.map(run_one, range(TOTAL_REQUESTS)))

    latencies = sorted(float(item["elapsed_s"]) for item in results)
    p95_index = max(0, min(len(latencies) - 1, int(0.95 * len(latencies)) - 1))
    p95 = latencies[p95_index]
    successes = sum(1 for item in results if item["ok"])
    app_results = [
        run_app_integration("Mitcham", "London Bridge"),
        run_app_integration("Mitcham", "King's Cross"),
    ]
    app_successes = sum(1 for item in app_results if item["ok"])
    app_p95_ms = round(max(float(item["elapsed_s"]) for item in app_results) * 1000, 1)

    receipt = {
        "event": "oap_routing_bounded_external_probe",
        "requests": TOTAL_REQUESTS,
        "workers": WORKERS,
        "successes": successes,
        "failures": TOTAL_REQUESTS - successes,
        "success_rate": round(successes / TOTAL_REQUESTS, 3),
        "p50_ms": round(statistics.median(latencies) * 1000, 1),
        "p95_ms": round(p95 * 1000, 1),
        "max_ms": round(max(latencies) * 1000, 1),
        "geometry_proven": all(bool(item["ok"]) for item in results),
        "bounded_capacity_proven": successes == TOTAL_REQUESTS and p95 <= P95_LIMIT_SECONDS,
        "dispatch_performed": False,
        "payment_performed": False,
        "tracking_performed": False,
        "oap_app_requests": len(app_results),
        "oap_app_successes": app_successes,
        "oap_app_integration_proven": app_successes == len(app_results),
        "oap_app_max_ms": app_p95_ms,
    }
    print(json.dumps(receipt, sort_keys=True))
    if successes != TOTAL_REQUESTS:
        raise SystemExit("live routing probe had failed requests")
    if p95 > P95_LIMIT_SECONDS:
        raise SystemExit(f"live routing probe p95 exceeded {P95_LIMIT_SECONDS}s")
    if app_successes != len(app_results):
        raise SystemExit("live OAP app routing integration probe failed")


if __name__ == "__main__":
    main()
