"""Bounded TfL authority road-disruption adapter for OAP Map Intelligence.

TfL is an external public authority data source, never OAP routing authority.
Responses are cached and bounded. Anonymous TfL access is supported at the
published low-rate tier; OAP_TFL_APP_KEY can be configured for higher quota.
"""
from __future__ import annotations

import json
import os
import threading
import time
from typing import Any
from urllib import parse as urlparse
from urllib import request as urlrequest

_API = "https://api.tfl.gov.uk/Road/all/Disruption"
_HOST = "api.tfl.gov.uk"
_TIMEOUT = 6
_MAX_BYTES = 2 * 1024 * 1024
_CACHE_SECONDS = 120
_LOCK = threading.Lock()
_CACHE_AT = 0.0
_CACHE: list[dict[str, Any]] = []
_LAST_ERROR: str | None = None


def _clean(value: object, limit: int) -> str:
    return " ".join(str(value or "").strip().split())[:limit]


def _fetch() -> list[dict[str, Any]]:
    global _CACHE_AT, _CACHE, _LAST_ERROR
    now = time.time()
    with _LOCK:
        if _CACHE and now - _CACHE_AT < _CACHE_SECONDS:
            return list(_CACHE)
    key = os.environ.get("OAP_TFL_APP_KEY", "").strip()
    url = _API + (("?" + urlparse.urlencode({"app_key": key})) if key else "")
    req = urlrequest.Request(url, headers={"Accept": "application/json", "User-Agent": "ON-ANY-POSTCODE-Map/1.0"})
    try:
        with urlrequest.urlopen(req, timeout=_TIMEOUT) as response:
            final = urlparse.urlparse(response.geturl())
            if final.scheme != "https" or final.hostname != _HOST:
                raise RuntimeError("tfl_redirect_rejected")
            body = response.read(_MAX_BYTES + 1)
        if len(body) > _MAX_BYTES:
            raise RuntimeError("tfl_response_too_large")
        payload = json.loads(body.decode("utf-8"))
        if not isinstance(payload, list):
            raise RuntimeError("invalid_tfl_response")
    except Exception as exc:  # fail closed; never break OAP routing
        with _LOCK:
            _LAST_ERROR = type(exc).__name__
        return []

    items: list[dict[str, Any]] = []
    for row in payload[:500]:
        if not isinstance(row, dict):
            continue
        geography = row.get("geography") if isinstance(row.get("geography"), dict) else {}
        coordinates = geography.get("coordinates") if isinstance(geography.get("coordinates"), list) else []
        items.append({
            "id": _clean(row.get("id"), 80),
            "road": _clean(row.get("location") or row.get("comments"), 180),
            "kind": _clean(row.get("category") or "disruption", 40).casefold(),
            "severity": _clean(row.get("severity"), 40),
            "note": _clean(row.get("currentUpdate") or row.get("comments"), 320),
            "status": _clean(row.get("status"), 40),
            "start_at": _clean(row.get("startDateTime"), 40),
            "end_at": _clean(row.get("endDateTime"), 40),
            "updated_at": _clean(row.get("currentUpdateDateTime") or row.get("lastModifiedTime"), 40),
            "has_closures": bool(row.get("hasClosures")),
            "corridor_ids": [str(v)[:30] for v in row.get("corridorIds", []) if isinstance(v, str)][:12],
            "coordinates": coordinates[:2] if len(coordinates) >= 2 else None,
            "source": "Transport for London Open Data",
            "confidence": "authority_feed",
            "authority_verified": True,
            "routing_effect": "advisory_only",
        })
    with _LOCK:
        _CACHE = items
        _CACHE_AT = now
        _LAST_ERROR = None
    return list(items)


def disruptions(query: object = None, *, roads: list[str] | None = None, limit: int = 30) -> list[dict[str, Any]]:
    items = _fetch()
    terms: list[str] = []
    q = _clean(query, 120).casefold()
    if q:
        terms.append(q)
    for road in roads or []:
        value = _clean(road, 120).casefold()
        if len(value) >= 2:
            terms.append(value)
    if terms:
        filtered = []
        for item in items:
            haystack = f"{item.get('road','')} {item.get('note','')} {' '.join(item.get('corridor_ids', []))}".casefold()
            if any(term in haystack or haystack in term for term in terms):
                filtered.append(item)
        items = filtered
    return items[: max(1, min(int(limit or 30), 50))]


def status() -> dict[str, object]:
    with _LOCK:
        cache_at = _CACHE_AT
        error = _LAST_ERROR
        count = len(_CACHE)
    return {
        "component": "TfL Road Authority Feed",
        "source": "Transport for London Open Data",
        "authority_verified_feed": True,
        "configured_key": bool(os.environ.get("OAP_TFL_APP_KEY", "").strip()),
        "anonymous_low_rate_supported": True,
        "cache_seconds": _CACHE_SECONDS,
        "cached_count": count,
        "last_fetch_epoch": int(cache_at) if cache_at else None,
        "last_error": error,
        "advisory_only": True,
        "automatic_rerouting": False,
        "dispatch": False,
        "payment_capture": False,
    }
