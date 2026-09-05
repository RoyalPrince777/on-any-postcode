"""Read-only proof helpers for OAP Movement.

This module fills the public Movement proof gap without dispatching people,
storing hidden location, charging money, or claiming confirmed bookings. It is
safe to expose because it works from explicit area strings only.
"""
from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
from math import asin, cos, radians, sin, sqrt

KNOWN_POINTS = {
    "mitcham": {"label": "Mitcham", "postcode": "CR4", "lat": 51.4036, "lon": -0.1687},
    "cr4": {"label": "Mitcham", "postcode": "CR4", "lat": 51.4036, "lon": -0.1687},
    "london bridge": {"label": "London Bridge", "postcode": "SE1", "lat": 51.5079, "lon": -0.0877},
    "se1": {"label": "London Bridge", "postcode": "SE1", "lat": 51.5079, "lon": -0.0877},
    "king's cross": {"label": "King's Cross", "postcode": "N1C", "lat": 51.5320, "lon": -0.1233},
    "kings cross": {"label": "King's Cross", "postcode": "N1C", "lat": 51.5320, "lon": -0.1233},
    "battersea": {"label": "Battersea", "postcode": "SW11", "lat": 51.4779, "lon": -0.1496},
    "sw11": {"label": "Battersea", "postcode": "SW11", "lat": 51.4779, "lon": -0.1496},
    "nunhead": {"label": "Nunhead", "postcode": "SE15", "lat": 51.4656, "lon": -0.0527},
    "se15": {"label": "Nunhead", "postcode": "SE15", "lat": 51.4656, "lon": -0.0527},
    "south london": {"label": "South London", "postcode": "SE / SW / CR", "lat": 51.4452, "lon": -0.1000},
    "begoro": {"label": "Begoro", "postcode": "Begoro", "lat": 6.3872, "lon": -0.3774},
    "koradaso": {"label": "KORADASO", "postcode": "KORADASO", "lat": 6.3872, "lon": -0.3774},
}

PROFILES = {
    "walking": {"speed_kmh": 4.8, "label": "Walking"},
    "cycling": {"speed_kmh": 15.0, "label": "Cycling"},
    "driving": {"speed_kmh": 32.0, "label": "Driving"},
    "transit": {"speed_kmh": 24.0, "label": "Public transport"},
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _norm(value: object) -> str:
    return " ".join(str(value or "").strip().lower().split())


def _point(value: object) -> dict[str, object]:
    key = _norm(value)
    if key in KNOWN_POINTS:
        return dict(KNOWN_POINTS[key])
    # No geocoding here: unknown areas remain accepted but unverified.
    label = str(value or "Unknown area").strip()[:120] or "Unknown area"
    return {"label": label, "postcode": "Not returned", "lat": None, "lon": None}


def _distance_km(a: dict[str, object], b: dict[str, object]) -> float | None:
    if None in {a.get("lat"), a.get("lon"), b.get("lat"), b.get("lon")}:
        return None
    lat1, lon1, lat2, lon2 = map(radians, [float(a["lat"]), float(a["lon"]), float(b["lat"]), float(b["lon"])])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    hav = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    return round(6371.0 * 2 * asin(sqrt(hav)), 2)


def route_proof(origin: object = "Mitcham", destination: object = "London Bridge", profile: object = "driving") -> dict[str, object]:
    """Return an explicit, public-safe route proof estimate."""

    generated_at = _now()
    start = _point(origin)
    end = _point(destination)
    profile_key = _norm(profile) or "driving"
    if profile_key not in PROFILES:
        profile_key = "driving"
    profile_data = PROFILES[profile_key]
    distance = _distance_km(start, end)
    verified = distance is not None
    minutes = None if distance is None else max(1, round((distance / float(profile_data["speed_kmh"])) * 60))
    proof_id = sha256(f"{generated_at}|{start['label']}|{end['label']}|{profile_key}".encode()).hexdigest()[:16]
    return {
        "component": "OAP Movement Route Proof",
        "proof_id": proof_id,
        "generated_at": generated_at,
        "public": True,
        "private_state_exposed": False,
        "origin": start,
        "destination": end,
        "profile": profile_key,
        "profile_label": profile_data["label"],
        "distance_km": distance,
        "estimated_minutes": minutes,
        "source": "OAP first-party seed coordinate estimate" if verified else "OAP query placeholder",
        "source_timestamp": generated_at,
        "route_geometry_exposed": False,
        "live_traffic_claim": False,
        "verified_area_pair": verified,
        "proof_status": "seed_route_proof" if verified else "needs_source_adapter",
        "movement_request_available": True,
        "direct_connection": True,
        "dispatch_enabled": False,
        "payment_capture_enabled": False,
        "confirmed_booking_enabled": False,
        "hidden_tracking": False,
        "green_gate": {
            "can_show_route_estimate": verified,
            "can_claim_live_traffic": False,
            "requires_osrm_or_equivalent_for_live_routing": True,
            "blocks_dispatch": True,
            "blocks_payment_capture": True,
            "blocks_hidden_tracking": True,
        },
    }


def request_receipt(payload: dict[str, object] | None = None) -> dict[str, object]:
    """Create a non-persistent request receipt for public-safe preview/API use."""

    body = dict(payload or {})
    generated_at = _now()
    origin = str(body.get("origin") or body.get("pickup") or "Mitcham")[:120]
    destination = str(body.get("destination") or "London Bridge")[:120]
    purpose = str(body.get("purpose") or "movement_request")[:80]
    route = route_proof(origin, destination, body.get("profile") or "driving")
    receipt_id = sha256(f"{generated_at}|{origin}|{destination}|{purpose}".encode()).hexdigest()[:16]
    return {
        "component": "OAP Movement Request Receipt",
        "receipt_id": receipt_id,
        "generated_at": generated_at,
        "status": "request_preview",
        "origin": origin,
        "destination": destination,
        "purpose": purpose,
        "route_proof": route,
        "hrm_receipt_required_for_persistence": True,
        "no_dispatch_triggered": True,
        "no_payment_taken": True,
        "no_hidden_tracking": True,
        "supplier_or_operator_required": True,
    }


def status() -> dict[str, object]:
    sample = route_proof("Mitcham", "London Bridge", "driving")
    return {
        "component": "Movement Proof + Request Layer",
        "public_route_proof": "/movement/route-proof",
        "public_request_preview": "/movement/request-preview",
        "sample": sample,
        "route_proof_ready": True,
        "request_preview_ready": True,
        "movement_to_direct_connected": True,
        "movement_to_atlas_connected": True,
        "consent_live_spot_boundary": "explicit opt-in only",
        "dispatch_enabled": False,
        "payment_capture_enabled": False,
        "confirmed_booking_enabled": False,
        "hidden_tracking": False,
        "next_gate": "Attach OSRM/local routing and durable HRM request receipts before operational dispatch can be considered.",
    }
