"""Live civilian World Crisis Intelligence for International Humanitarian Intelligence.

This module reads authoritative public crisis sources for civilian humanitarian awareness.
It does not create targeting, surveillance, military command, autonomous dispatch, or legal
adjudication authority. External source failures fail closed and are surfaced explicitly.
"""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime, timedelta
from typing import Any
from urllib import parse as urlparse
from urllib import request as urlrequest

GDACS_ENDPOINT = "https://www.gdacs.org/gdacsapi/api/events/geteventlist/SEARCH"

WORLD_CRISIS_CATEGORIES: tuple[dict[str, str], ...] = (
    {"id": "armed_conflict", "name": "Armed Conflict & Complex Emergency"},
    {"id": "natural_hazard", "name": "Natural Hazard & Disaster"},
    {"id": "health", "name": "Public Health Emergency"},
    {"id": "displacement", "name": "Displacement & Refugee Emergency"},
    {"id": "food_water", "name": "Food, Water & Essential Needs Crisis"},
    {"id": "connectivity", "name": "Connectivity & Critical Infrastructure Crisis"},
    {"id": "environment", "name": "Environmental & Climate Emergency"},
    {"id": "multi_system", "name": "Multi-system Humanitarian Crisis"},
)

AUTHORITATIVE_SOURCE_REGISTRY: tuple[dict[str, Any], ...] = (
    {
        "id": "gdacs",
        "name": "Global Disaster Alert and Coordination System",
        "owner": "United Nations / European Commission cooperation framework",
        "role": "Live sudden-onset disaster alerts and geospatial hazard evidence",
        "machine_readable": True,
        "production_fetch": True,
        "auth_required": False,
    },
    {
        "id": "who",
        "name": "World Health Organization Emergencies",
        "owner": "World Health Organization",
        "role": "Authoritative health emergencies, outbreak news and situation reports",
        "machine_readable": True,
        "production_fetch": True,
        "auth_required": False,
    },
    {
        "id": "unhcr",
        "name": "UNHCR Global Public API / Operational Data Portal",
        "owner": "UNHCR",
        "role": "Refugee, displacement and statelessness data",
        "machine_readable": True,
        "production_fetch": True,
        "auth_required": False,
    },
    {
        "id": "reliefweb",
        "name": "ReliefWeb API",
        "owner": "OCHA",
        "role": "Curated humanitarian reports, disasters and country context",
        "machine_readable": True,
        "production_fetch": False,
        "auth_required": False,
        "activation_requirement": "pre_approved_appname",
    },
)

GDACS_EVENT_TYPES: tuple[str, ...] = ("EQ", "TC", "FL", "VO", "DR", "WF")
GDACS_ALERT_LEVELS: tuple[str, ...] = ("Orange", "Red")
ALERT_PRIORITY: dict[str, int] = {"Red": 0, "Orange": 1, "Green": 2}


def _bounded_timeout() -> float:
    raw = os.environ.get("OAP_WORLD_CRISIS_TIMEOUT_SECONDS", "4").strip()
    try:
        value = float(raw)
    except ValueError:
        value = 4.0
    return min(max(value, 1.0), 10.0)


def _fetch_json(url: str, *, timeout: float) -> dict[str, Any]:
    request = urlrequest.Request(
        url,
        headers={
            "Accept": "application/geo+json, application/json",
            "User-Agent": "OAP-World-Crisis-Intelligence/1.0",
        },
    )
    with urlrequest.urlopen(request, timeout=timeout) as response:
        if getattr(response, "status", 200) != 200:
            raise RuntimeError(f"source_http_{getattr(response, 'status', 'unknown')}")
        body = response.read(2_000_000)
    payload = json.loads(body.decode("utf-8"))
    if not isinstance(payload, dict):
        raise TypeError("source_payload_not_object")
    return payload


def _coarse_geometry(feature: dict[str, Any]) -> dict[str, float] | None:
    geometry = feature.get("geometry")
    if not isinstance(geometry, dict):
        return None
    coordinates = geometry.get("coordinates")
    if geometry.get("type") == "Point" and isinstance(coordinates, list) and len(coordinates) >= 2:
        try:
            longitude = round(float(coordinates[0]), 3)
            latitude = round(float(coordinates[1]), 3)
        except (TypeError, ValueError):
            return None
        return {"latitude": latitude, "longitude": longitude}
    return None


def _normalise_gdacs_feature(feature: dict[str, Any]) -> dict[str, Any] | None:
    properties = feature.get("properties")
    if not isinstance(properties, dict):
        return None
    event_id = properties.get("eventid")
    event_type = str(properties.get("eventtype") or "").upper()
    alert_level = str(properties.get("alertlevel") or "").title()
    if not event_id or event_type not in GDACS_EVENT_TYPES:
        return None
    affected = properties.get("affectedcountries")
    countries: list[str] = []
    if isinstance(affected, list):
        for item in affected:
            if isinstance(item, dict):
                name = str(item.get("countryname") or "").strip()
                if name:
                    countries.append(name)
    if not countries:
        country = str(properties.get("country") or "").strip()
        if country:
            countries.append(country)
    return {
        "source": "gdacs",
        "source_event_id": str(event_id),
        "category": "natural_hazard",
        "event_type": event_type,
        "name": str(properties.get("name") or properties.get("eventname") or event_type).strip(),
        "alert_level": alert_level or "Unknown",
        "alert_score": properties.get("alertscore"),
        "countries": tuple(dict.fromkeys(countries)),
        "from_date": properties.get("fromdate"),
        "to_date": properties.get("todate"),
        "geometry": _coarse_geometry(feature),
        "civilian_only": True,
        "targeting": False,
        "surveillance": False,
    }


def fetch_gdacs_crises(
    *,
    now: datetime | None = None,
    lookback_days: int = 7,
    timeout: float | None = None,
) -> dict[str, Any]:
    """Fetch recent Orange/Red GDACS events and return a bounded normalized snapshot."""

    current = now.astimezone(UTC) if now else datetime.now(UTC)
    days = min(max(int(lookback_days), 1), 30)
    start = (current - timedelta(days=days)).date().isoformat()
    end = current.date().isoformat()
    query = urlparse.urlencode(
        {
            "eventlist": ",".join(GDACS_EVENT_TYPES),
            "fromDate": start,
            "toDate": end,
            "alertlevel": ";".join(GDACS_ALERT_LEVELS),
            "pageSize": "100",
            "pageNumber": "1",
        }
    )
    url = f"{GDACS_ENDPOINT}?{query}"
    try:
        payload = _fetch_json(url, timeout=_bounded_timeout() if timeout is None else timeout)
    except Exception as exc:  # noqa: BLE001 -- source boundary must fail closed
        return {
            "source": "gdacs",
            "live": False,
            "error": type(exc).__name__,
            "event_count": 0,
            "events": (),
            "fetched_at": current.isoformat(),
        }
    features = payload.get("features")
    if not isinstance(features, list):
        return {
            "source": "gdacs",
            "live": False,
            "error": "invalid_geojson_feature_collection",
            "event_count": 0,
            "events": (),
            "fetched_at": current.isoformat(),
        }
    events = tuple(
        event
        for event in (_normalise_gdacs_feature(item) for item in features if isinstance(item, dict))
        if event is not None
    )
    ordered = tuple(
        sorted(
            events,
            key=lambda item: (
                ALERT_PRIORITY.get(str(item["alert_level"]), 9),
                str(item.get("to_date") or ""),
            ),
        )
    )
    return {
        "source": "gdacs",
        "live": True,
        "error": None,
        "event_count": len(ordered),
        "events": ordered,
        "fetched_at": current.isoformat(),
    }


def world_crisis_snapshot(*, live_fetch: bool = True) -> dict[str, Any]:
    """Return the multi-source civilian humanitarian emergency snapshot."""

    from .humanitarian_emergency_tracker import humanitarian_emergency_snapshot

    return humanitarian_emergency_snapshot(live_fetch=live_fetch)


def world_crisis_intelligence_status() -> dict[str, Any]:
    """Return architecture and source readiness without making a network request."""

    category_ids = tuple(item["id"] for item in WORLD_CRISIS_CATEGORIES)
    source_ids = tuple(item["id"] for item in AUTHORITATIVE_SOURCE_REGISTRY)
    architecture_ready = (
        len(category_ids) == 8
        and len(category_ids) == len(set(category_ids))
        and len(source_ids) == 4
        and len(source_ids) == len(set(source_ids))
    )
    return {
        "id": "world_crisis_emergency",
        "name": "World Crisis Emergency Intelligence",
        "parent": "International Humanitarian Intelligence",
        "mode": "live_civilian_crisis_awareness",
        "demo_mode": False,
        "architecture_ready": architecture_ready,
        "category_count": len(WORLD_CRISIS_CATEGORIES),
        "categories": WORLD_CRISIS_CATEGORIES,
        "source_count": len(AUTHORITATIVE_SOURCE_REGISTRY),
        "sources": AUTHORITATIVE_SOURCE_REGISTRY,
        "live_machine_source_enabled": "gdacs",
        "live_machine_sources_enabled": ("gdacs", "who", "unhcr"),
        "who_emergency_context_ready": True,
        "unhcr_context_ready": True,
        "gdacs_emergency_fetch_ready": True,
        "who_emergency_fetch_ready": True,
        "unhcr_displacement_context_ready": True,
        "reliefweb_requires_preapproved_appname": True,
        "multi_source_tracker_bound": True,
        "map_ready": True,
        "legal_intelligence_bound": True,
        "civilian_only": True,
        "precise_civilian_location_public": False,
        "individual_tracking": False,
        "military_overlays": False,
        "targeting": False,
        "surveillance": False,
        "autonomous_dispatch": False,
        "autonomous_broadcast": False,
        "independent_execute": False,
        "independent_approval": False,
        "human_authority_final": True,
        "truth_boundary": (
            "World Crisis Intelligence delegates live snapshots to the governed International "
            "Humanitarian Emergency Tracker. GDACS, WHO and UNHCR source availability is verified "
            "at runtime; ReliefWeb remains gated until a pre-approved appname is configured."
        ),
    }
