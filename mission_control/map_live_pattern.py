"""Bounded first-party Live Pattern reports for Map Intelligence.

These are OAP/community reports, not authority-certified traffic feeds. Reports
expire automatically, store no precise device location, and never alter routing,
dispatch, payment or Founder state.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from threading import Lock
from uuid import uuid4

_LOCK = Lock()
_REPORTS: list[dict[str, object]] = []
_TTL = timedelta(hours=2)
_MAX_REPORTS = 100
_ALLOWED_KINDS = {"closure", "hazard", "delay", "crowd", "event", "roadworks"}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _clean(value: object, limit: int) -> str:
    return " ".join(str(value or "").strip().split())[:limit]


def _prune(now: datetime) -> None:
    cutoff = now - _TTL
    _REPORTS[:] = [r for r in _REPORTS if isinstance(r.get("created_at_dt"), datetime) and r["created_at_dt"] >= cutoff]


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


def reports(query: object = None) -> list[dict[str, object]]:
    now = _now()
    term = _clean(query, 100).casefold()
    with _LOCK:
        _prune(now)
        items = list(_REPORTS)
    if term:
        items = [r for r in items if term in f"{r.get('area','')} {r.get('road','')} {r.get('note','')}".casefold()]
    return [{k: v for k, v in r.items() if k != "created_at_dt"} for r in items[:30]]


def status() -> dict[str, object]:
    now = _now()
    with _LOCK:
        _prune(now)
        count = len(_REPORTS)
    return {
        "component": "OAP Live Pattern",
        "active_report_count": count,
        "ttl_minutes": int(_TTL.total_seconds() // 60),
        "authority_verified_feed": False,
        "community_reports_enabled": True,
        "advisory_only": True,
        "hidden_tracking": False,
        "precise_device_location_stored": False,
        "automatic_rerouting": False,
    }
