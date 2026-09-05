"""Governed live/open-data source helpers for OAP Atlas.

This module prepares a controlled, opt-in live source layer for Atlas. It is
server-side only, query-based only, timeout-bound and attribution-bound. It does
not track users, does not store private location, does not dispatch, does not
capture payment, and does not import external marketplace authority.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from typing import Iterable

MAX_RESULTS = 12
TIMEOUT_SECONDS = 5
DEFAULT_USER_AGENT = "ON-ANY-POSTCODE-Atlas/1.0 founder-governed-place-lookup"
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
ALLOWED_PLACE_FIELDS = (
    "place_id",
    "licence",
    "osm_type",
    "osm_id",
    "lat",
    "lon",
    "display_name",
    "class",
    "type",
    "importance",
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _enabled() -> bool:
    return os.environ.get("OAP_ATLAS_OPEN_DATA_ENABLED", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def _safe_query(query: object) -> str:
    value = " ".join(str(query or "").strip().split())
    if len(value) > 120:
        value = value[:120]
    return value or "Mitcham"


def _category_for(item: dict[str, object]) -> str:
    klass = str(item.get("class") or "").lower()
    kind = str(item.get("type") or "").lower()
    if klass in {"amenity", "shop"}:
        return "shops" if klass == "shop" else "food"
    if klass in {"tourism", "historic"}:
        return "attractions"
    if klass in {"leisure", "natural"}:
        return "parks_nature"
    if klass in {"railway", "highway", "public_transport"}:
        return "transport_movement"
    if "hotel" in kind or "guest" in kind or "hostel" in kind:
        return "stays_venues"
    return "oap_direct"


def status() -> dict[str, object]:
    enabled = _enabled()
    return {
        "component": "OAP Atlas Live Source Adapter",
        "adapter": "OpenStreetMap / Nominatim",
        "enabled": enabled,
        "state": "enabled" if enabled else "configured_locked",
        "signal": "yellow" if enabled else "locked",
        "generated_at": _now(),
        "public_safe": True,
        "private_state_exposed": False,
        "hidden_tracking": False,
        "stores_user_location": False,
        "uses_precise_user_location": False,
        "query_based_only": True,
        "timeout_seconds": TIMEOUT_SECONDS,
        "max_results": MAX_RESULTS,
        "requires_attribution": True,
        "requires_source_timestamp": True,
        "external_provider_authority": False,
        "payment_capture_enabled": False,
        "dispatch_enabled": False,
        "confirmed_booking_enabled": False,
        "live_claim_allowed": enabled,
        "enable_env": "OAP_ATLAS_OPEN_DATA_ENABLED=true",
    }


def _sanitise_items(items: Iterable[dict[str, object]], fetched_at: str) -> list[dict[str, object]]:
    clean: list[dict[str, object]] = []
    for raw in items:
        if not isinstance(raw, dict):
            continue
        item = {field: raw.get(field) for field in ALLOWED_PLACE_FIELDS if field in raw}
        name = str(item.get("display_name") or "").strip()
        if not name:
            continue
        item.update(
            name=name.split(",")[0][:120],
            category=_category_for(item),
            source="OpenStreetMap / Nominatim",
            source_tier="openstreetmap",
            source_timestamp=fetched_at,
            source_backed=True,
            live_source_backed=True,
            proof_lane="green",
            freshness="live_request_timestamped",
            confidence="source_backed",
            can_show_publicly=True,
            can_claim_live=True,
            no_hidden_tracking=True,
            movement_ready=True,
            direct_request_available=True,
            external_provider_authority=False,
            oap_certified=False,
        )
        clean.append(item)
        if len(clean) >= MAX_RESULTS:
            break
    return clean


def fetch_places(query: object) -> dict[str, object]:
    """Fetch public place candidates only when explicitly enabled by env."""

    fetched_at = _now()
    query_value = _safe_query(query)
    base = status()
    if not base["enabled"]:
        return {
            **base,
            "query": query_value,
            "fetched_at": None,
            "fetch_status": "disabled_by_environment",
            "results": [],
            "result_count": 0,
            "can_claim_live_now": False,
        }

    params = urllib.parse.urlencode(
        {
            "q": query_value,
            "format": "jsonv2",
            "addressdetails": "0",
            "limit": str(MAX_RESULTS),
        }
    )
    request = urllib.request.Request(
        f"{NOMINATIM_URL}?{params}",
        headers={"User-Agent": os.environ.get("OAP_ATLAS_USER_AGENT", DEFAULT_USER_AGENT)},
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            payload = response.read(96_000).decode("utf-8", errors="replace")
        parsed = json.loads(payload)
        results = _sanitise_items(parsed if isinstance(parsed, list) else [], fetched_at)
        return {
            **base,
            "query": query_value,
            "fetched_at": fetched_at,
            "fetch_status": "success",
            "results": results,
            "result_count": len(results),
            "attribution": "© OpenStreetMap contributors",
            "can_claim_live_now": len(results) > 0,
        }
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, UnicodeError) as exc:
        return {
            **base,
            "query": query_value,
            "fetched_at": fetched_at,
            "fetch_status": "failed_safe",
            "error": type(exc).__name__,
            "results": [],
            "result_count": 0,
            "can_claim_live_now": False,
        }
