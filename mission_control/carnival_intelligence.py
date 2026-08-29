"""Governed, read-only Notting Hill Carnival intelligence for OAP World.

This first release contains reviewed public schedule and orientation data only.
It does not make runtime provider calls, infer crowd conditions, track people,
collect location, calculate routes or claim that scheduled information is live.
External map loading is an explicit visitor choice handled by the public UI.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import datetime
from typing import Any
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo

EVENT_TIMEZONE = ZoneInfo("Europe/London")
EVENT_WINDOW_START = datetime(2026, 8, 29, 11, 0, tzinfo=EVENT_TIMEZONE)
EVENT_WINDOW_END = datetime(2026, 9, 1, 6, 0, tzinfo=EVENT_TIMEZONE)
DATA_REVIEWED_ON = "2026-08-28"

MAP = {
    "title": "Notting Hill Carnival area orientation",
    "description": (
        "A street-map orientation view for the wider Carnival area. The official "
        "event map remains the source of truth for routes and facilities."
    ),
    "embed_url": (
        "https://www.openstreetmap.org/export/embed.html?"
        "bbox=-0.2200%2C51.5050%2C-0.1840%2C51.5320&layer=mapnik"
    ),
    "open_url": "https://www.openstreetmap.org/#map=15/51.5185/-0.2020",
    "provider": "OpenStreetMap contributors",
    "loads_automatically": False,
    "uses_device_location": False,
    "route_geometry": False,
}

SOURCES: tuple[dict[str, str], ...] = (
    {
        "id": "nhc-map",
        "name": "Notting Hill Carnival official map",
        "url": "https://nhcarnival.org/maps",
        "publisher": "Notting Hill Carnival",
        "source_updated_on": "Not stated",
        "reviewed_on": DATA_REVIEWED_ON,
    },
    {
        "id": "rbkc-event-map",
        "name": "Carnival event map",
        "url": (
            "https://www.rbkc.gov.uk/parks-leisure-and-culture/"
            "filming-and-special-events/notting-hill-carnival/carnival-event-map"
        ),
        "publisher": "Royal Borough of Kensington and Chelsea",
        "source_updated_on": "2026-08-28",
        "reviewed_on": DATA_REVIEWED_ON,
    },
    {
        "id": "rbkc-schedule",
        "name": "Official event schedule",
        "url": (
            "https://www.rbkc.gov.uk/parks-leisure-and-culture/"
            "filming-and-special-events/notting-hill-carnival/"
            "official-event-schedule"
        ),
        "publisher": "Royal Borough of Kensington and Chelsea",
        "source_updated_on": "2026-07-30",
        "reviewed_on": DATA_REVIEWED_ON,
    },
    {
        "id": "rbkc-roads",
        "name": "Road closures and parking restrictions",
        "url": (
            "https://www.rbkc.gov.uk/parks-leisure-and-culture/"
            "filming-and-special-events/notting-hill-carnival/"
            "road-closures-and-parking-restrictions"
        ),
        "publisher": "Royal Borough of Kensington and Chelsea",
        "source_updated_on": "2026-08-28",
        "reviewed_on": DATA_REVIEWED_ON,
    },
    {
        "id": "tfl-travel",
        "name": "Carnival and Bank Holiday travel 2026",
        "url": (
            "https://tfl.gov.uk/status-updates/major-works-and-events/"
            "notting-hill-carnival-and-august-bank-holiday-travel-2026"
        ),
        "publisher": "Transport for London",
        "source_updated_on": "2026 event guidance",
        "reviewed_on": DATA_REVIEWED_ON,
    },
    {
        "id": "nhc-safety",
        "name": "Carnival safety guidance",
        "url": "https://nhcarnival.org/safety",
        "publisher": "Notting Hill Carnival",
        "source_updated_on": "Not stated",
        "reviewed_on": DATA_REVIEWED_ON,
    },
    {
        "id": "nhc-accessibility",
        "name": "Carnival accessibility guidance",
        "url": "https://nhcarnival.org/accessibility",
        "publisher": "Notting Hill Carnival",
        "source_updated_on": "Not stated",
        "reviewed_on": DATA_REVIEWED_ON,
    },
)

SCHEDULE: tuple[dict[str, Any], ...] = (
    {
        "id": "saturday",
        "date": "Saturday 29 August 2026",
        "theme": "Steel band competition day",
        "source_id": "rbkc-schedule",
        "items": (
            {
                "time": "16:00–00:00",
                "name": "UK National Panorama Steel Band Competition",
                "place": "Emslie Horniman’s Pleasance, Kensal Road, W10 3DH",
                "claim": "scheduled",
            },
        ),
    },
    {
        "id": "sunday",
        "date": "Sunday 30 August 2026",
        "theme": "Family and children’s day",
        "source_id": "rbkc-schedule",
        "items": (
            {
                "time": "06:00–09:00",
                "name": "J’Ouvert traditional celebration",
                "place": "Starts at Sainsbury’s, Canal Way, W10 5AA",
                "claim": "scheduled",
            },
            {
                "time": "10:00–10:30",
                "name": "Official opening ceremony",
                "place": "MAS Judging Point, Great Western Road",
                "claim": "scheduled",
            },
            {
                "time": "10:00–18:00",
                "name": "Children’s Day Parade",
                "place": "Official parade route",
                "claim": "scheduled",
            },
            {
                "time": "10:00–20:00",
                "name": "Street trading in Kensington and Chelsea",
                "place": "Official Carnival area",
                "claim": "scheduled",
            },
        ),
    },
    {
        "id": "monday",
        "date": "Monday 31 August 2026",
        "theme": "Adults’ day",
        "source_id": "rbkc-schedule",
        "items": (
            {
                "time": "10:30",
                "name": "Parade begins",
                "place": "Official parade route",
                "claim": "scheduled",
            },
            {
                "time": "12:00–19:00",
                "name": "Static sound systems",
                "place": "Official mapped locations",
                "claim": "scheduled",
            },
            {
                "time": "10:00–20:00",
                "name": "Street trading in Kensington and Chelsea",
                "place": "Official Carnival area",
                "claim": "scheduled",
            },
        ),
    },
)

LAYERS: tuple[dict[str, str], ...] = (
    {
        "id": "parade",
        "icon": "🥁",
        "name": "Parade route",
        "description": "Route and judging-zone locations from the official event map.",
        "source_id": "rbkc-event-map",
        "claim": "official-map-category",
    },
    {
        "id": "music",
        "icon": "🔊",
        "name": "Stages and sound systems",
        "description": "Official mapped stage and static sound-system locations.",
        "source_id": "nhc-map",
        "claim": "official-map-category",
    },
    {
        "id": "trading",
        "icon": "🍲",
        "name": "Street traders and shops",
        "description": (
            "Official street-trading areas and times. Individual shop opening "
            "hours are not supplied or represented as current."
        ),
        "source_id": "rbkc-event-map",
        "claim": "official-map-category",
    },
    {
        "id": "welfare",
        "icon": "💚",
        "name": "Medical and welfare",
        "description": "First-aid, medical and official welfare support locations.",
        "source_id": "nhc-safety",
        "claim": "official-guidance",
    },
    {
        "id": "facilities",
        "icon": "♿",
        "name": "Toilets and accessibility",
        "description": "Temporary toilets, accessible units and mobility guidance.",
        "source_id": "nhc-accessibility",
        "claim": "official-guidance",
    },
    {
        "id": "travel",
        "icon": "🚇",
        "name": "Travel and exits",
        "description": "Station restrictions, step-free options and road closures.",
        "source_id": "tfl-travel",
        "claim": "official-guidance",
    },
    {
        "id": "safety",
        "icon": "🛡️",
        "name": "Public safety",
        "description": (
            "Public help guidance only—never officer positions, surveillance "
            "outputs or tactical information."
        ),
        "source_id": "nhc-safety",
        "claim": "official-guidance",
    },
)

TRAVEL_ALERTS: tuple[dict[str, str], ...] = (
    {
        "level": "Important",
        "title": "Paddington is the recommended lower-crowd arrival",
        "detail": "TfL recommends Paddington and the signed walking route.",
        "source_id": "tfl-travel",
    },
    {
        "level": "Closed",
        "title": "Ladbroke Grove station",
        "detail": "Closed all day on Sunday and Monday.",
        "source_id": "tfl-travel",
    },
    {
        "level": "Restricted",
        "title": "Notting Hill Gate station",
        "detail": (
            "No entry 11:00–18:00; District and Circle line trains do not stop."
        ),
        "source_id": "tfl-travel",
    },
    {
        "level": "Restricted",
        "title": "Westbourne Park station",
        "detail": "No entry from 11:00 on Sunday and Monday.",
        "source_id": "tfl-travel",
    },
    {
        "level": "Roads",
        "title": "Extensive Carnival-area closures",
        "detail": "Most closures run 06:00 Sunday to 06:00 Tuesday.",
        "source_id": "rbkc-roads",
    },
    {
        "level": "Accessibility",
        "title": "Step-free options via Paddington",
        "detail": "TfL lists step-free and boarding-ramp options; check before travel.",
        "source_id": "tfl-travel",
    },
)

WELFARE_LOCATIONS: tuple[str, ...] = (
    "Powis Square",
    "Emslie Horniman’s Pleasance Gardens (north end)",
    "Shrewsbury Gardens",
    "Venture Community Centre, Faraday Road",
)

PUBLIC_BOUNDARY: dict[str, bool] = {
    "live_people_tracking": False,
    "live_child_tracking": False,
    "live_officer_tracking": False,
    "facial_recognition_data": False,
    "precise_location_collection": False,
    "background_location_collection": False,
    "crowd_inference": False,
    "automated_rerouting": False,
    "dispatch": False,
    "payments": False,
}

EXPECTED_SOURCE_IDS = {
    "nhc-map",
    "rbkc-event-map",
    "rbkc-schedule",
    "rbkc-roads",
    "tfl-travel",
    "nhc-safety",
    "nhc-accessibility",
}
EXPECTED_LAYER_IDS = {
    "parade",
    "music",
    "trading",
    "welfare",
    "facilities",
    "travel",
    "safety",
}
ALLOWED_SOURCE_HOSTS = {
    "nhcarnival.org",
    "www.rbkc.gov.uk",
    "tfl.gov.uk",
}


def _phase(now: datetime | None = None) -> dict[str, str]:
    current = now or datetime.now(EVENT_TIMEZONE)
    if current.tzinfo is None:
        raise ValueError("timezone_required")
    localized = current.astimezone(EVENT_TIMEZONE)
    if localized < EVENT_WINDOW_START:
        return {
            "id": "scheduled",
            "label": "Scheduled information",
            "message": "The event window has not started. Check official sources again.",
        }
    if localized <= EVENT_WINDOW_END:
        return {
            "id": "event-window",
            "label": "Event window · scheduled data",
            "message": (
                "Carnival may be active, but OAP has no verified live feed. "
                "Check official sources and on-site instructions."
            ),
        }
    return {
        "id": "archive",
        "label": "Archived 2026 information",
        "message": "This event window has ended. Do not use these details for travel.",
    }


def validate_carnival_hub(
    *,
    sources: Iterable[Mapping[str, str]] = SOURCES,
    schedule: Iterable[Mapping[str, Any]] = SCHEDULE,
    layers: Iterable[Mapping[str, str]] = LAYERS,
    travel_alerts: Iterable[Mapping[str, str]] = TRAVEL_ALERTS,
    public_boundary: Mapping[str, bool] = PUBLIC_BOUNDARY,
    map_config: Mapping[str, Any] = MAP,
) -> dict[str, Any]:
    """Reject incomplete, unapproved or misleading Carnival projections."""

    source_items = tuple(sources)
    schedule_items = tuple(schedule)
    layer_items = tuple(layers)
    alert_items = tuple(travel_alerts)
    source_ids = [str(item.get("id", "")) for item in source_items]
    layer_ids = [str(item.get("id", "")) for item in layer_items]
    errors: list[str] = []

    if set(source_ids) != EXPECTED_SOURCE_IDS or len(source_ids) != len(
        EXPECTED_SOURCE_IDS
    ):
        errors.append("Carnival sources must match the reviewed official allowlist")
    if len(source_ids) != len(set(source_ids)):
        errors.append("Duplicate Carnival source IDs")
    if set(layer_ids) != EXPECTED_LAYER_IDS or len(layer_ids) != len(
        EXPECTED_LAYER_IDS
    ):
        errors.append("Carnival layers must match the bounded first-release scope")
    if len(layer_ids) != len(set(layer_ids)):
        errors.append("Duplicate Carnival layer IDs")

    for source in source_items:
        parsed = urlsplit(str(source.get("url", "")))
        if parsed.scheme != "https" or parsed.hostname not in ALLOWED_SOURCE_HOSTS:
            errors.append(f"Unapproved Carnival source: {source.get('name')}")

    if len(schedule_items) != 3 or {item.get("id") for item in schedule_items} != {
        "saturday",
        "sunday",
        "monday",
    }:
        errors.append("Carnival schedule must contain the three reviewed event days")
    for day in schedule_items:
        if day.get("source_id") not in EXPECTED_SOURCE_IDS:
            errors.append(f"Schedule day has no reviewed source: {day.get('id')}")
        for item in tuple(day.get("items", ())):
            if item.get("claim") != "scheduled":
                errors.append(f"Schedule item is mislabelled as live: {item.get('name')}")

    for item in (*layer_items, *alert_items):
        if item.get("source_id") not in EXPECTED_SOURCE_IDS:
            errors.append(f"Unreviewed source reference: {item.get('source_id')}")

    embed = urlsplit(str(map_config.get("embed_url", "")))
    open_map = urlsplit(str(map_config.get("open_url", "")))
    if (
        embed.scheme != "https"
        or embed.hostname != "www.openstreetmap.org"
        or embed.path != "/export/embed.html"
        or open_map.scheme != "https"
        or open_map.hostname != "www.openstreetmap.org"
    ):
        errors.append("The optional map must use the approved OpenStreetMap surface")
    if map_config.get("loads_automatically") or map_config.get(
        "uses_device_location"
    ):
        errors.append("The public map must be opt-in and location-free")
    if map_config.get("route_geometry"):
        errors.append("Route geometry is not approved for Carnival v0")
    if any(bool(value) for value in public_boundary.values()):
        errors.append("Carnival v0 must remain read-only and tracking-free")

    return {
        "passed": not errors,
        "errors": errors,
        "checks": {
            "official_sources": len(source_items),
            "schedule_days": len(schedule_items),
            "public_layers": len(layer_items),
            "travel_alerts": len(alert_items),
            "runtime_provider_calls": 0,
            "live_feeds": 0,
        },
    }


def get_public_carnival_hub(now: datetime | None = None) -> dict[str, Any]:
    """Return a bounded public projection containing no personal information."""

    sources = {item["id"]: dict(item) for item in SOURCES}
    return {
        "event": {
            "name": "Notting Hill Carnival 2026",
            "place": "Notting Hill, west London",
            "timezone": "Europe/London",
            "valid_from": EVENT_WINDOW_START.isoformat(),
            "valid_until": EVENT_WINDOW_END.isoformat(),
            "phase": _phase(now),
        },
        "evidence": {
            "rating": "Official scheduled sources · no live feed",
            "reviewed_on": DATA_REVIEWED_ON,
            "human_review_required": True,
            "stale_data_fails_closed": True,
        },
        "map": dict(MAP),
        "schedule": tuple(
            {
                **{key: value for key, value in day.items() if key != "items"},
                "items": tuple(dict(item) for item in day["items"]),
            }
            for day in SCHEDULE
        ),
        "layers": tuple(dict(item) for item in LAYERS),
        "travel_alerts": tuple(dict(item) for item in TRAVEL_ALERTS),
        "welfare_locations": WELFARE_LOCATIONS,
        "sources": tuple(dict(item) for item in SOURCES),
        "sources_by_id": sources,
        "boundary": dict(PUBLIC_BOUNDARY),
        "live_feed_available": False,
    }
