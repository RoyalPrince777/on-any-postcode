"""Bounded Live Pattern intelligence for Map Intelligence.

Community reports remain advisory. OAP also reads current London road
disruptions from Transport for London Open Data. TfL supports anonymous
low-rate API access; an optional OAP_TFL_API_KEY can raise quota. The authority
feed is read-only, bounded, cached, and never dispatches, charges, tracks a
device, or automatically changes a route.
"""
from __future__ import annotations

import json
import os
import time
from datetime import datetime, timedelta, timezone
from threading import Lock
from urllib import error as urlerror
from urllib import parse as urlparse
from urllib import request as urlrequest
from uuid import uuid4

_LOCK = Lock()
_REPORTS: list[dict[str, object]] = []
_TTL = timedelta(hours=2)
_MAX_REPORTS = 100
_ALLOWED_KINDS = {"closure", "hazard", "delay", "crowd", "event", "roadworks"}

_TFL_HOST = "api.tfl.gov.uk"
_TFL_CACHE_SECONDS = 300
_TFL_MAX_BYTES = 2 * 1024 * 1024
_TFL_TIMEOUT_SECONDS = 6
_TFL_CACHE: tuple[float, list[dict[str, object]]] = (0.0, [])
_TFL_LAST_SUCCESS: float | None = None
_TFL_LAST_ERROR: str | None = None


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _clean(value: object, limit: int) -> str:
    return " ".join(str(value or "").strip().split())[:limit]


def _prune(now: datetime) -> None:
    cutoff = now - _TTL
    _REPORTS[:] = [r for r in _REPORTS if isinstance(r.get("created_at_dt"), datetime) and r["created_at_dt"] >= cutoff]


def _tfl_key() -> str:
    return str(os.environ.get("OAP_TFL_API_KEY") or os.environ.get("OAP_TFL_APP_KEY") or "").strip()


def authority_feed_configured() -> bool:
    """TfL anonymous low-rate access means the authority feed needs no secret."""
    return True


def _severity_kind(value: object) -> str:
    text = _clean(value, 80).casefold()
    if "closed" in text or "closure" in text:
        return "closure"
    if "roadwork" in text or "works" in text:
        return "roadworks"
    if "hazard" in text or "incident" in text or "collision" in text:
        return "hazard"
    return "delay"


def _normalise_tfl(item: object) -> dict[str, object] | None:
    if not isinstance(item, dict):
        return None
    road = _clean(item.get("location") or item.get("corridorIds") or item.get("category"), 140)
    area = _clean(item.get("boroughs") or item.get("location") or "Greater London", 120)
    description = _clean(item.get("currentUpdate") or item.get("comments") or item.get("category"), 320)
    severity = _clean(item.get("severity") or item.get("severityDescription"), 80)
    identifier = _clean(item.get("id"), 100)
    geography = item.get("geography") if isinstance(item.get("geography"), dict) else {}
    coordinates = geography.get("coordinates") if isinstance(geography.get("coordinates"), list) else None
    if not road and not description:
        return None
    return {
        "id": identifier or f"tfl-{abs(hash((road, description))) % 10**12}",
        "area": area or "Greater London",
        "road": road or "London road network",
        "kind": _severity_kind(f"{severity} {description}"),
        "note": description,
        "severity": severity,
        "status": _clean(item.get("status"), 40),
        "has_closures": bool(item.get("hasClosures")),
        "coordinates": coordinates[:2] if isinstance(coordinates, list) and len(coordinates) >= 2 else None,
        "start_at": _clean(item.get("startDateTime"), 40),
        "end_at": _clean(item.get("endDateTime"), 40),
        "updated_at": _clean(item.get("currentUpdateDateTime") or item.get("lastModifiedTime"), 40),
        "source": "Transport for London Open Data",
        "confidence": "authority_feed",
        "authority_verified": True,
        "routing_effect": "advisory_only",
    }


def authority_reports(query: object = None) -> list[dict[str, object]]:
    global _TFL_CACHE, _TFL_LAST_SUCCESS, _TFL_LAST_ERROR
    key = _tfl_key()
    now_epoch = time.time()
    cached_at, cached_items = _TFL_CACHE
    if cached_items and now_epoch - cached_at < _TFL_CACHE_SECONDS:
        items = list(cached_items)
    else:
        params = urlparse.urlencode({"app_key": key}) if key else ""
        url = f"https://{_TFL_HOST}/Road/All/Disruption" + (f"?{params}" if params else "")
        req = urlrequest.Request(url, headers={"Accept": "application/json", "User-Agent": "ON-ANY-POSTCODE-Map/1.0"})
        try:
            with urlrequest.urlopen(req, timeout=_TFL_TIMEOUT_SECONDS) as response:
                final = urlparse.urlparse(response.geturl())
                if final.scheme != "https" or final.hostname != _TFL_HOST:
                    raise RuntimeError("tfl_redirect_rejected")
                body = response.read(_TFL_MAX_BYTES + 1)
            if len(body) > _TFL_MAX_BYTES:
                raise RuntimeError("tfl_response_too_large")
            payload = json.loads(body.decode("utf-8"))
            if not isinstance(payload, list):
                raise TypeError("tfl_invalid_response")
            items = []
            for raw in payload[:500]:
                normalised = _normalise_tfl(raw)
                if normalised:
                    items.append(normalised)
            _TFL_CACHE = (now_epoch, items)
            _TFL_LAST_SUCCESS = now_epoch
            _TFL_LAST_ERROR = None
        except (urlerror.URLError, OSError, RuntimeError, TypeError, ValueError, UnicodeError) as exc:
            _TFL_LAST_ERROR = type(exc).__name__
            return []
    term = _clean(query, 100).casefold()
    if term:
        items = [r for r in items if term in f"{r.get('area','')} {r.get('road','')} {r.get('note','')}".casefold()]
    return items[:60]


def add_report(*, area: object, road: object, kind: object, note: object) -> dict[str, object]:
    now = _now()
    area_v = _clean(area, 100)
    road_v = _clean(road, 120)
    note_v = _clean(note, 240)
    kind_v = _clean(kind, 24).casefold()
    if len(area_v) < 2 or len(road_v) < 2:
        raise ValueError("area_and_road_required")
    if kind_v not in _ALLOWED_KINDS:
        raise ValueError("invalid_live_pattern_kind")
    report = {
        "id": uuid4().hex[:16],
        "area": area_v,
        "road": road_v,
        "kind": kind_v,
        "note": note_v,
        "source": "OAP community report",
        "confidence": "unverified_report",
        "authority_verified": False,
        "routing_effect": "advisory_only",
        "created_at": now.isoformat().replace("+00:00", "Z"),
        "expires_at": (now + _TTL).isoformat().replace("+00:00", "Z"),
        "created_at_dt": now,
    }
    with _LOCK:
        _prune(now)
        _REPORTS.insert(0, report)
        del _REPORTS[_MAX_REPORTS:]
    return {k: v for k, v in report.items() if k != "created_at_dt"}


def community_reports(query: object = None) -> list[dict[str, object]]:
    now = _now()
    term = _clean(query, 100).casefold()
    with _LOCK:
        _prune(now)
        items = list(_REPORTS)
    if term:
        items = [r for r in items if term in f"{r.get('area','')} {r.get('road','')} {r.get('note','')}".casefold()]
    return [{k: v for k, v in r.items() if k != "created_at_dt"} for r in items[:30]]


def reports(query: object = None) -> list[dict[str, object]]:
    """Authority items first, then bounded community reports."""
    return (authority_reports(query) + community_reports(query))[:80]


def status() -> dict[str, object]:
    now = _now()
    with _LOCK:
        _prune(now)
        count = len(_REPORTS)
    authority_verified = _TFL_LAST_SUCCESS is not None and _TFL_LAST_ERROR is None
    return {
        "component": "OAP Live Pattern",
        "active_report_count": count,
        "ttl_minutes": int(_TTL.total_seconds() // 60),
        "authority_feed": "Transport for London Open Data",
        "authority_feed_configured": True,
        "authority_key_configured": bool(_tfl_key()),
        "authority_anonymous_low_rate": not bool(_tfl_key()),
        "authority_verified_feed": authority_verified,
        "authority_last_success_epoch": int(_TFL_LAST_SUCCESS) if _TFL_LAST_SUCCESS is not None else None,
        "authority_last_error": _TFL_LAST_ERROR,
        "authority_cache_seconds": _TFL_CACHE_SECONDS,
        "community_reports_enabled": True,
        "advisory_only": True,
        "hidden_tracking": False,
        "precise_device_location_stored": False,
        "automatic_rerouting": False,
    }
