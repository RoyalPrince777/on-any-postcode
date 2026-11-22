"""Strict same-host, read-only quote bridge to OAP Ride Phase 1.

No shared authentication, driver dispatch, booking, money movement or fake live state.
"""
from __future__ import annotations

import json
import math
import os
from urllib import parse, request as urlrequest

from flask import Blueprint, jsonify, make_response, request

from . import web_security

bp = Blueprint("oap_ride_backend_bridge", __name__)


class BackendUnavailable(Exception):
    """The first-party backend has not supplied valid proof."""


class _NoRedirect(urlrequest.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


_OPENER = urlrequest.build_opener(urlrequest.ProxyHandler({}), _NoRedirect())


def _origin() -> str:
    raw = os.environ.get("OAP_RIDE_BACKEND_URL", "").strip()
    try:
        parts = parse.urlsplit(raw)
        if not (
            parts.scheme == "http"
            and parts.hostname in {"127.0.0.1", "localhost", "::1"}
            and parts.port is not None
            and not parts.username
            and not parts.password
            and not parts.path.strip("/")
            and not parts.query
            and not parts.fragment
        ):
            raise BackendUnavailable("backend_not_configured")
    except ValueError as exc:
        raise BackendUnavailable("invalid_backend_configuration") from exc
    return raw.rstrip("/")


def _read(path: str, body: dict | None = None) -> dict:
    base = _origin()
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urlrequest.Request(
        base + path, data=data,
        headers={"Accept": "application/json", **(
            {"Content-Type": "application/json"} if data is not None else {}
        )},
        method="POST" if data is not None else "GET",
    )
    try:
        with _OPENER.open(req, timeout=1.8) as response:
            if response.status != 200:
                raise BackendUnavailable("backend_not_ready")
            raw = response.read(32769)
        if len(raw) > 32768:
            raise BackendUnavailable("oversized_backend_response")
        value = json.loads(raw)
        if not isinstance(value, dict):
            raise BackendUnavailable("invalid_backend_response")
        return value
    except (OSError, ValueError, TypeError) as exc:
        raise BackendUnavailable("backend_unavailable") from exc


def _reply(value: dict, code: int = 200):
    response = make_response(jsonify(value), code)
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


def _blocked():
    return _reply({
        "connected": False, "status": "unknown", "quote_ready": False,
        "dispatch_authorised": False, "payment_authorised": False,
        "production_ready": False,
    }, 503)


@bp.get("/transport/ride/backend/status")
def status():
    try:
        health = _read("/healthz")
        readiness = _read("/v1/platform/readiness")
    except BackendUnavailable:
        return _blocked()
    if (health.get("service") != "oap_ride_phase1"
            or health.get("status") != "database_and_redis_ready"
            or readiness.get("phase") != 1):
        return _blocked()
    return _reply({
        "connected": True,
        "status": "database_and_redis_ready",
        "routing_configured": health.get("route_engine_configured") is True,
        "quote_ready": False,
        "demo_mode": health.get("demo_mode") is True,
        "dispatch_authorised": False,
        "payment_authorised": False,
        "production_ready": False,
        "booking_owner": "/movement/workspace",
    })


@bp.get("/transport/ride/backend/places")
def places():
    term = " ".join(str(request.args.get("q") or "").split())
    if not 2 <= len(term) <= 80:
        return _reply({"results": [], "source": "local_only"}, 400)
    try:
        data = _read("/v1/places?" + parse.urlencode({"q": term}))
    except BackendUnavailable:
        return _blocked()
    if data.get("geocoder") != "local_seed_only" or not isinstance(data.get("results"), list):
        return _blocked()
    results = []
    for item in data["results"][:8]:
        if not isinstance(item, dict):
            continue
        label = str(item.get("label") or "").strip()[:120]
        if not label:
            continue
        point = {"label": label}
        lat, lon = item.get("lat"), item.get("lon")
        if (type(lat) in (int, float) and type(lon) in (int, float)
                and math.isfinite(lat) and math.isfinite(lon)
                and -90 <= lat <= 90 and -180 <= lon <= 180):
            point.update({"lat": lat, "lon": lon})
        results.append(point)
    return _reply({"results": results, "source": "self_hosted_seed",
                   "full_geocoding_ready": False})


@bp.post("/transport/ride/backend/quote")
def quote():
    if not web_security.csrf_valid(request):
        return _reply({"error": "csrf_failed"}, 403)
    if request.content_length is not None and request.content_length > 1024:
        return _reply({"error": "invalid_request"}, 400)
    body = request.get_json(silent=True)
    if not isinstance(body, dict) or body.get("vehicle_class") not in {"car", "ebike"}:
        return _reply({"error": "invalid_request"}, 400)
    validated = {"vehicle_class": body["vehicle_class"]}
    for field in ("pickup_lat", "pickup_lon", "drop_lat", "drop_lon"):
        v = body.get(field)
        limit = 90 if field.endswith("_lat") else 180
        if (type(v) not in (int, float) or not math.isfinite(v)
                or not -limit <= v <= limit):
            return _reply({"error": "invalid_coordinates"}, 400)
        validated[field] = float(v)
    if not web_security.PUBLIC_WRITE_LIMITER.allow(
        "ride_quote:" + str(request.remote_addr or "unknown")
    ):
        return _reply({"error": "rate_limited"}, 429)
    try:
        data = _read("/v1/rides/quote", validated)
    except BackendUnavailable:
        return _blocked()
    amount, distance, duration = (
        data.get("amount_minor"), data.get("distance_m"), data.get("duration_s")
    )
    if (data.get("source") != "self_hosted_osrm"
            or data.get("quote_status") != "estimate_not_firm_fare"
            or data.get("currency") != "GBP"
            or type(amount) is not int or not 0 < amount < 10_000_000
            or type(distance) is not int or distance <= 0
            or type(duration) is not int or duration <= 0
            or data.get("licensed_payment_connected") is not False
            or data.get("live_dispatch_confirmed") is not False):
        return _blocked()
    return _reply({
        "amount_minor": amount, "currency": "GBP", "distance_m": distance,
        "duration_s": duration, "source": "self_hosted_osrm",
        "quote_status": "estimate_not_firm_fare", "live_dispatch_confirmed": False,
        "licensed_payment_connected": False,
    })
