"""Public-safe live humanitarian projection for OAP Pulse.

This module adapts the governed International Humanitarian Emergency Tracker for
public Pulse display. It does not persist external facts into the user post
store, infer severity, expose precise civilian locations, or create warnings.
"""

from __future__ import annotations

from collections.abc import Mapping
from urllib.parse import urljoin, urlparse

from . import humanitarian_emergency_tracker

MAX_PUBLIC_EVENTS = 20
_ALLOWED_EVENT_SOURCES = {"gdacs", "who_don"}
_SOURCE_NAMES = {
    "gdacs": "GDACS",
    "who_don": "WHO Disease Outbreak News",
    "unhcr_nowcasting": "UNHCR displacement context",
    "reliefweb": "ReliefWeb",
}
_SOURCE_HOME = {
    "gdacs": "https://www.gdacs.org/",
    "who_don": "https://www.who.int/emergencies/disease-outbreak-news",
    "unhcr_nowcasting": "https://www.unhcr.org/refugee-statistics/",
    "reliefweb": "https://reliefweb.int/",
}
_CATEGORY_NAMES = {
    "natural_hazard": "Natural hazard / disaster",
    "health": "Public health",
}


def _clean(value: object, *, limit: int) -> str:
    return " ".join(str(value or "").split())[:limit]


def _safe_source_url(source: str, value: object) -> str:
    raw = _clean(value, limit=400)
    if source == "who_don" and raw.startswith("/"):
        raw = urljoin("https://www.who.int", raw)
    parsed = urlparse(raw)
    if parsed.scheme == "https" and parsed.netloc:
        return raw
    return _SOURCE_HOME.get(source, "")


def _event_projection(item: Mapping[str, object]) -> dict[str, object] | None:
    source = _clean(item.get("source"), limit=40)
    if source not in _ALLOWED_EVENT_SOURCES:
        return None
    if item.get("civilian_only") is not True:
        return None
    if item.get("targeting") is True or item.get("surveillance") is True:
        return None

    name = _clean(item.get("name"), limit=180)
    source_event_id = _clean(item.get("source_event_id"), limit=120)
    if not name or not source_event_id:
        return None

    countries = tuple(
        country
        for country in (
            _clean(value, limit=80) for value in tuple(item.get("countries") or ())[:8]
        )
        if country
    )
    summary = _clean(item.get("summary"), limit=360)
    return {
        "source": source,
        "source_name": _SOURCE_NAMES[source],
        "source_event_id": source_event_id,
        "name": name,
        "category": _CATEGORY_NAMES.get(
            _clean(item.get("category"), limit=60),
            _clean(item.get("category"), limit=60) or "Humanitarian",
        ),
        "alert_level": _clean(item.get("alert_level"), limit=40) or "Source update",
        "countries": countries,
        "countries_text": ", ".join(countries) if countries else "International",
        "observed_at": _clean(item.get("from_date") or item.get("to_date"), limit=64),
        "summary": summary,
        "source_url": _safe_source_url(source, item.get("source_url")),
        "truth": "Observed source record",
    }


def _source_states(snapshot: Mapping[str, object]) -> tuple[dict[str, object], ...]:
    states = snapshot.get("source_states")
    source_states = states if isinstance(states, Mapping) else {}
    output: list[dict[str, object]] = []
    for source in ("gdacs", "who_don", "unhcr_nowcasting", "reliefweb"):
        raw = source_states.get(source)
        state = raw if isinstance(raw, Mapping) else {}
        live = state.get("live") is True
        configured = state.get("configured") is True
        if source == "reliefweb":
            status = "gated" if not live else "live"
        else:
            status = "live" if live else "unavailable"
        output.append(
            {
                "source": source,
                "name": _SOURCE_NAMES[source],
                "status": status,
                "live": live,
                "configured": configured,
                "source_url": _SOURCE_HOME[source],
            }
        )
    return tuple(output)


def public_snapshot(*, live_fetch: bool = True) -> dict[str, object]:
    """Return the public-safe humanitarian Pulse snapshot.

    External source failures fail closed. No event is stored in Pulse persistence.
    """

    try:
        snapshot = humanitarian_emergency_tracker.humanitarian_emergency_snapshot(
            live_fetch=live_fetch
        )
    except Exception:  # noqa: BLE001 - public source boundary must fail closed.
        return {
            "ready": False,
            "event_count": 0,
            "events": (),
            "live_sources": (),
            "source_states": (),
            "fetched_at": "",
            "refresh_seconds": 180,
            "civilian_only": True,
            "source_backed_only": True,
            "precise_civilian_location": False,
            "individual_tracking": False,
            "autonomous_warning": False,
        }

    events: list[dict[str, object]] = []
    for raw in tuple(snapshot.get("events") or ()):
        if not isinstance(raw, Mapping):
            continue
        projected = _event_projection(raw)
        if projected is not None:
            events.append(projected)
        if len(events) >= MAX_PUBLIC_EVENTS:
            break

    try:
        refresh_seconds = int(snapshot.get("cache_seconds") or 180)
    except (TypeError, ValueError):
        refresh_seconds = 180
    refresh_seconds = min(max(refresh_seconds, 60), 900)

    live_sources = tuple(
        source
        for source in tuple(snapshot.get("live_sources") or ())
        if str(source) in {"gdacs", "who_don", "unhcr_nowcasting"}
    )
    return {
        "ready": bool(live_sources),
        "event_count": len(events),
        "events": tuple(events),
        "live_sources": live_sources,
        "source_states": _source_states(snapshot),
        "fetched_at": _clean(snapshot.get("fetched_at"), limit=64),
        "refresh_seconds": refresh_seconds,
        "civilian_only": True,
        "source_backed_only": True,
        "precise_civilian_location": False,
        "individual_tracking": False,
        "autonomous_warning": False,
    }
