"""Live civilian-only international humanitarian emergency tracker.

The tracker combines authoritative public emergency sources into a bounded OAP
world-state projection. It is designed for civilian protection, humanitarian
awareness and research only. It never creates military overlays, target lists,
individual tracking, autonomous dispatch or autonomous public warnings.
"""

from __future__ import annotations

import html
import json
import os
import re
import threading
import time
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from typing import Any
from urllib import parse as urlparse
from urllib import request as urlrequest

from . import world_crisis_intelligence

WHO_DON_ENDPOINT = "https://www.who.int/api/emergencies/diseaseoutbreaknews"
UNHCR_NOWCAST_ENDPOINT = "https://api.unhcr.org/population/v1/nowcasting/"
RELIEFWEB_ENDPOINT = "https://api.reliefweb.int/v2/disasters"

TRACKER_REVISION = "2026-09-04-v1"
DEFAULT_CACHE_SECONDS = 180
MAX_EVENTS = 80
MAX_SOURCE_ITEMS = 50

_SOURCE_REGISTRY: tuple[dict[str, object], ...] = (
    {
        "id": "gdacs",
        "name": "GDACS",
        "owner": "United Nations / European Commission cooperation framework",
        "role": "Sudden-onset hazard and disaster alerts",
        "production_fetch": True,
        "credentials_required": False,
    },
    {
        "id": "who_don",
        "name": "WHO Disease Outbreak News",
        "owner": "World Health Organization",
        "role": "Confirmed or potential acute public-health events of concern",
        "production_fetch": True,
        "credentials_required": False,
    },
    {
        "id": "unhcr_nowcasting",
        "name": "UNHCR Refugee Data Finder nowcasting",
        "owner": "UNHCR",
        "role": "Current displacement context; not an emergency alert feed",
        "production_fetch": True,
        "credentials_required": False,
    },
    {
        "id": "reliefweb",
        "name": "ReliefWeb API",
        "owner": "OCHA",
        "role": "Curated humanitarian disaster/report context",
        "production_fetch": False,
        "credentials_required": False,
        "activation_requirement": "pre_approved_appname",
    },
)

_ALERT_ORDER = {"Red": 0, "Orange": 1, "WHO Update": 2, "Unknown": 9}
_TAG_RE = re.compile(r"<[^>]+>")
_UUIDISH_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f-]{27,}$", re.IGNORECASE)
_CACHE_LOCK = threading.Lock()
_CACHE: dict[str, object] = {"at": 0.0, "snapshot": None}


def _cache_seconds() -> int:
    raw = os.environ.get("OAP_HUMANITARIAN_TRACKER_CACHE_SECONDS", str(DEFAULT_CACHE_SECONDS))
    try:
        value = int(raw)
    except ValueError:
        value = DEFAULT_CACHE_SECONDS
    return min(max(value, 30), 900)


def _timeout_seconds() -> float:
    raw = os.environ.get("OAP_HUMANITARIAN_SOURCE_TIMEOUT_SECONDS", "4")
    try:
        value = float(raw)
    except ValueError:
        value = 4.0
    return min(max(value, 1.0), 10.0)


def _fetch_json(url: str, *, timeout: float | None = None) -> object:
    request = urlrequest.Request(
        url,
        headers={
            "Accept": "application/json, application/geo+json",
            "User-Agent": "OAP-Humanitarian-Emergency-Tracker/1.0",
        },
    )
    with urlrequest.urlopen(request, timeout=timeout or _timeout_seconds()) as response:
        status = getattr(response, "status", 200)
        if status != 200:
            raise RuntimeError(f"source_http_{status}")
        body = response.read(2_000_000)
    return json.loads(body.decode("utf-8"))


def _items(payload: object) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload[:MAX_SOURCE_ITEMS] if isinstance(item, dict)]
    if not isinstance(payload, dict):
        return []
    for key in ("value", "items", "results", "data"):
        value = payload.get(key)
        if isinstance(value, list):
            return [item for item in value[:MAX_SOURCE_ITEMS] if isinstance(item, dict)]
    return []


def _clean_text(value: object, *, limit: int = 320) -> str:
    text = html.unescape(_TAG_RE.sub(" ", str(value or "")))
    return " ".join(text.split())[:limit]


def _date_text(item: Mapping[str, object]) -> str | None:
    for key in ("PublicationDate", "publication_date", "date", "DateCreated", "LastModified"):
        value = item.get(key)
        if value:
            return str(value)[:64]
    return None


def _human_readable_countries(value: object) -> tuple[str, ...]:
    countries: list[str] = []
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        for item in value:
            if isinstance(item, Mapping):
                candidate = item.get("name") or item.get("countryname") or item.get("country")
            else:
                candidate = item
            text = _clean_text(candidate, limit=80)
            if text and not _UUIDISH_RE.match(text):
                countries.append(text)
    elif value:
        text = _clean_text(value, limit=120)
        if text and not _UUIDISH_RE.match(text):
            for candidate in re.split(r"[,;/|]", text):
                cleaned = candidate.strip()
                if cleaned:
                    countries.append(cleaned[:80])
    return tuple(dict.fromkeys(countries))


def fetch_who_outbreaks() -> dict[str, object]:
    """Fetch recent WHO Disease Outbreak News without inferring clinical severity."""

    query = urlparse.urlencode({"$top": "40", "$orderby": "PublicationDate desc"})
    current = datetime.now(UTC).isoformat()
    try:
        payload = _fetch_json(f"{WHO_DON_ENDPOINT}?{query}")
        rows = _items(payload)
    except Exception as exc:  # noqa: BLE001 -- external source boundary fails closed
        return {
            "source": "who_don",
            "live": False,
            "error": type(exc).__name__,
            "event_count": 0,
            "events": (),
            "fetched_at": current,
        }

    events: list[dict[str, object]] = []
    for row in rows:
        source_id = row.get("DonId") or row.get("SystemSourceKey") or row.get("UrlName")
        title = _clean_text(row.get("Title") or row.get("Name") or row.get("UrlName"), limit=180)
        if not source_id or not title:
            continue
        summary = _clean_text(
            row.get("Summary") or row.get("Overview") or row.get("Response"), limit=360
        )
        countries = _human_readable_countries(
            row.get("countries") or row.get("regionscountries") or row.get("Country")
        )
        events.append(
            {
                "source": "who_don",
                "source_event_id": str(source_id)[:120],
                "category": "health",
                "event_type": "WHO_DON",
                "name": title,
                "alert_level": "WHO Update",
                "countries": countries,
                "from_date": _date_text(row),
                "to_date": None,
                "geometry": None,
                "summary": summary,
                "source_url": str(row.get("ItemDefaultUrl") or "")[:300],
                "observed_or_inferred": "observed",
                "civilian_only": True,
                "targeting": False,
                "surveillance": False,
            }
        )
    return {
        "source": "who_don",
        "live": True,
        "error": None,
        "event_count": len(events),
        "events": tuple(events),
        "fetched_at": current,
    }


def fetch_unhcr_displacement_context() -> dict[str, object]:
    """Fetch bounded UNHCR nowcasting context without treating estimates as alerts."""

    current = datetime.now(UTC).isoformat()
    query = urlparse.urlencode({"limit": "20", "page": "1"})
    try:
        payload = _fetch_json(f"{UNHCR_NOWCAST_ENDPOINT}?{query}")
        rows = _items(payload)
    except Exception as exc:  # noqa: BLE001 -- external source boundary fails closed
        return {
            "source": "unhcr_nowcasting",
            "live": False,
            "error": type(exc).__name__,
            "row_count": 0,
            "latest_year": None,
            "fetched_at": current,
        }

    years: list[int] = []
    for row in rows:
        for key in ("year", "Year", "year_to", "yearTo"):
            try:
                if row.get(key) is not None:
                    years.append(int(row[key]))
            except (TypeError, ValueError):
                pass
    return {
        "source": "unhcr_nowcasting",
        "live": bool(rows),
        "error": None if rows else "empty_response",
        "row_count": len(rows),
        "latest_year": max(years) if years else None,
        "fetched_at": current,
        "classification": "displacement_context_not_alert",
        "individual_records": False,
    }


def reliefweb_source_state() -> dict[str, object]:
    appname = os.environ.get("OAP_RELIEFWEB_APPNAME", "").strip()
    return {
        "source": "reliefweb",
        "live": False,
        "configured": bool(appname),
        "error": None if appname else "preapproved_appname_required",
        "production_fetch_enabled": False,
        "endpoint": RELIEFWEB_ENDPOINT,
    }


def _deduplicate(events: Sequence[Mapping[str, object]]) -> tuple[dict[str, object], ...]:
    seen: set[tuple[str, str]] = set()
    output: list[dict[str, object]] = []
    for item in events:
        key = (str(item.get("source") or ""), str(item.get("source_event_id") or ""))
        if not all(key) or key in seen:
            continue
        seen.add(key)
        output.append(dict(item))
    output.sort(
        key=lambda item: (
            _ALERT_ORDER.get(str(item.get("alert_level") or "Unknown"), 8),
            str(item.get("from_date") or item.get("to_date") or ""),
        ),
        reverse=False,
    )
    return tuple(output[:MAX_EVENTS])


def _category_counts(events: Sequence[Mapping[str, object]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for event in events:
        category = str(event.get("category") or "unknown")
        counts[category] = counts.get(category, 0) + 1
    return counts


def _country_counts(events: Sequence[Mapping[str, object]]) -> tuple[dict[str, object], ...]:
    counts: dict[str, int] = {}
    for event in events:
        for country in event.get("countries") or ():
            name = str(country).strip()
            if name:
                counts[name] = counts.get(name, 0) + 1
    ordered = sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:20]
    return tuple({"country": country, "event_count": count} for country, count in ordered)


def _matrix_events(events: Sequence[Mapping[str, object]]) -> tuple[dict[str, object], ...]:
    output: list[dict[str, object]] = []
    for event in events:
        geometry = event.get("geometry")
        coarse_geometry = dict(geometry) if isinstance(geometry, Mapping) else None
        output.append(
            {
                "event_type": "humanitarian_emergency_signal",
                "source": event.get("source"),
                "source_event_id": event.get("source_event_id"),
                "category": event.get("category"),
                "name": event.get("name"),
                "alert_level": event.get("alert_level"),
                "countries": tuple(event.get("countries") or ()),
                "geometry": coarse_geometry,
                "observed_or_inferred": "observed",
                "civilian_only": True,
                "precise_civilian_location": False,
                "targeting": False,
                "surveillance": False,
            }
        )
    return tuple(output)


def _build_snapshot(*, live_fetch: bool) -> dict[str, object]:
    current = datetime.now(UTC).isoformat()
    if live_fetch:
        gdacs = world_crisis_intelligence.fetch_gdacs_crises()
        who = fetch_who_outbreaks()
        unhcr = fetch_unhcr_displacement_context()
    else:
        gdacs = {
            "source": "gdacs",
            "live": False,
            "error": "live_fetch_disabled",
            "event_count": 0,
            "events": (),
            "fetched_at": current,
        }
        who = {
            "source": "who_don",
            "live": False,
            "error": "live_fetch_disabled",
            "event_count": 0,
            "events": (),
            "fetched_at": current,
        }
        unhcr = {
            "source": "unhcr_nowcasting",
            "live": False,
            "error": "live_fetch_disabled",
            "row_count": 0,
            "latest_year": None,
            "fetched_at": current,
        }
    reliefweb = reliefweb_source_state()
    events = _deduplicate(tuple(gdacs.get("events", ())) + tuple(who.get("events", ())))
    live_sources = tuple(
        source
        for source, state in (
            ("gdacs", gdacs),
            ("who_don", who),
            ("unhcr_nowcasting", unhcr),
        )
        if state.get("live") is True
    )
    return {
        "id": "international_humanitarian_emergency_tracker",
        "name": "International Humanitarian Emergency Tracker",
        "revision": TRACKER_REVISION,
        "parent": "International Humanitarian Intelligence",
        "mode": "live_civilian_multi_source_tracking",
        "demo_mode": False,
        "tracking_ready": bool(live_sources),
        "live_data_ready": bool(live_sources),
        "live_source_count": len(live_sources),
        "live_sources": live_sources,
        "source_states": {
            "gdacs": gdacs,
            "who_don": who,
            "unhcr_nowcasting": unhcr,
            "reliefweb": reliefweb,
        },
        "gdacs": gdacs,
        "who": who,
        "unhcr": unhcr,
        "reliefweb": reliefweb,
        "event_count": len(events),
        "events": events,
        "category_counts": _category_counts(events),
        "country_counts": _country_counts(events),
        "matrix_events": _matrix_events(events),
        "fetched_at": current,
        "cache_seconds": _cache_seconds(),
        "live_on_request": True,
        "dashboard_auto_refresh": True,
        "background_autonomous_dispatch": False,
        "civilian_only": True,
        "source_verification_required": True,
        "observed_vs_inferred_labels": True,
        "precise_civilian_location_public": False,
        "individual_tracking": False,
        "crowd_tracking": False,
        "military_overlays": False,
        "targeting": False,
        "surveillance": False,
        "weapons_support": False,
        "autonomous_dispatch": False,
        "autonomous_public_warning": False,
        "human_authority_final": True,
    }


def humanitarian_emergency_snapshot(
    *, live_fetch: bool = True, force: bool = False
) -> dict[str, object]:
    """Return a cached live civilian emergency snapshot."""

    if not live_fetch:
        return _build_snapshot(live_fetch=False)
    now = time.monotonic()
    with _CACHE_LOCK:
        cached = _CACHE.get("snapshot")
        age = now - float(_CACHE.get("at") or 0.0)
        if not force and isinstance(cached, dict) and age < _cache_seconds():
            result = dict(cached)
            result["cache_hit"] = True
            result["cache_age_seconds"] = round(age, 2)
            return result
    snapshot = _build_snapshot(live_fetch=True)
    snapshot["cache_hit"] = False
    snapshot["cache_age_seconds"] = 0.0
    with _CACHE_LOCK:
        _CACHE["snapshot"] = dict(snapshot)
        _CACHE["at"] = time.monotonic()
    return snapshot


def humanitarian_emergency_tracker_status() -> dict[str, object]:
    """Return architecture/source readiness without performing network I/O."""

    source_ids = tuple(str(item["id"]) for item in _SOURCE_REGISTRY)
    architecture_ready = len(source_ids) == len(set(source_ids)) == 4
    return {
        "id": "international_humanitarian_emergency_tracker",
        "name": "International Humanitarian Emergency Tracker",
        "revision": TRACKER_REVISION,
        "mode": "live_civilian_multi_source_tracking",
        "architecture_ready": architecture_ready,
        "sources": _SOURCE_REGISTRY,
        "source_count": len(_SOURCE_REGISTRY),
        "gdacs_live_fetch_enabled": True,
        "who_live_fetch_enabled": True,
        "unhcr_live_context_enabled": True,
        "reliefweb_preapproved_appname_required": True,
        "matrix_world_state_ready": True,
        "founder_dashboard_ready": True,
        "smi_context_ready": True,
        "civilian_only": True,
        "precise_civilian_location_public": False,
        "individual_tracking": False,
        "military_overlays": False,
        "targeting": False,
        "surveillance": False,
        "autonomous_dispatch": False,
        "autonomous_public_warning": False,
        "human_authority_final": True,
        "truth_boundary": (
            "The tracker may fetch authoritative public civilian emergency data from GDACS, "
            "WHO and UNHCR. ReliefWeb remains gated until a pre-approved appname is configured. "
            "Source availability is verified at runtime and failures fail closed."
        ),
    }


# Compatibility for the existing SMI crisis-context call path.
def world_crisis_snapshot(*, live_fetch: bool = True) -> dict[str, object]:
    return humanitarian_emergency_snapshot(live_fetch=live_fetch)
