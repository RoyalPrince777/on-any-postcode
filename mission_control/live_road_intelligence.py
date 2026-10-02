"""Truth-gated live road intelligence for OAP Map Intelligence.

Aggregates fresh authority/community road signals and bounded, consent-originated
movement observations. It never turns missing evidence into a live claim.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from threading import Lock
from uuid import uuid4

from . import map_live_pattern

_LOCK = Lock()
_OBSERVATIONS: list[dict[str, object]] = []
_OBSERVATION_TTL = timedelta(minutes=10)
_MAX_OBSERVATIONS = 1000
_ALLOWED_STATES = {"free", "slow", "heavy", "stopped", "closed", "hazard", "unknown"}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _clean(value: object, limit: int) -> str:
    return " ".join(str(value or "").strip().split())[:limit]


def _prune(now: datetime) -> None:
    cutoff = now - _OBSERVATION_TTL
    _OBSERVATIONS[:] = [
        item for item in _OBSERVATIONS
        if isinstance(item.get("observed_at_dt"), datetime) and item["observed_at_dt"] >= cutoff
    ]


def record_observation(*, road: object, state: object, speed_kph: object = None, source: object = "consented_device") -> dict[str, object]:
    road_v = _clean(road, 140)
    state_v = _clean(state, 20).casefold()
    source_v = _clean(source, 40) or "consented_device"
    if len(road_v) < 2:
        raise ValueError("road_required")
    if state_v not in _ALLOWED_STATES - {"unknown"}:
        raise ValueError("invalid_road_state")
    speed = None
    if speed_kph not in (None, ""):
        speed = max(0.0, min(250.0, float(speed_kph)))
    now = _now()
    item = {
        "id": uuid4().hex[:16],
        "road": road_v,
        "state": state_v,
        "speed_kph": speed,
        "source": source_v,
        "observed_at": now.isoformat().replace("+00:00", "Z"),
        "expires_at": (now + _OBSERVATION_TTL).isoformat().replace("+00:00", "Z"),
        "observed_at_dt": now,
        "precise_device_location_stored": False,
    }
    with _LOCK:
        _prune(now)
        _OBSERVATIONS.insert(0, item)
        del _OBSERVATIONS[_MAX_OBSERVATIONS:]
    return {k: v for k, v in item.items() if k != "observed_at_dt"}


def observations(road: object = None) -> list[dict[str, object]]:
    now = _now()
    term = _clean(road, 140).casefold()
    with _LOCK:
        _prune(now)
        items = list(_OBSERVATIONS)
    if term:
        items = [item for item in items if term in str(item.get("road") or "").casefold()]
    return [{k: v for k, v in item.items() if k != "observed_at_dt"} for item in items[:200]]


def _severity(kind: object, *, closure: bool = False) -> tuple[str, float]:
    text = _clean(kind, 40).casefold()
    if closure or text == "closure":
        return "closed", 2.0
    if text in {"hazard", "roadworks"}:
        return "hazard", 1.45
    if text in {"delay", "crowd", "event"}:
        return "heavy", 1.25
    return "unknown", 1.0


def route_state(route: object, query: object = None) -> dict[str, object]:
    route_v = route if isinstance(route, dict) else {}
    roads = [str(x).strip() for x in (route_v.get("roads") or []) if str(x).strip()]
    reports = map_live_pattern.reports(query)
    matched: list[dict[str, object]] = []
    multiplier = 1.0
    strongest = "unknown"
    rank = {"unknown": 0, "free": 1, "slow": 2, "heavy": 3, "hazard": 4, "stopped": 5, "closed": 6}

    for report in reports:
        hay = f"{report.get('road','')} {report.get('area','')} {report.get('note','')}".casefold()
        if roads and not any(road.casefold() in hay or hay.find(road.casefold()) >= 0 for road in roads):
            continue
        state, factor = _severity(report.get("kind"), closure=bool(report.get("has_closures")))
        multiplier = max(multiplier, factor)
        if rank[state] > rank[strongest]:
            strongest = state
        matched.append({
            "id": report.get("id"),
            "road": report.get("road"),
            "kind": report.get("kind"),
            "state": state,
            "source": report.get("source"),
            "authority_verified": bool(report.get("authority_verified")),
            "updated_at": report.get("updated_at") or report.get("created_at"),
        })

    road_terms = {road.casefold() for road in roads}
    obs = observations()
    matched_obs: list[dict[str, object]] = []
    for item in obs:
        road = str(item.get("road") or "")
        if road_terms and not any(term in road.casefold() or road.casefold() in term for term in road_terms):
            continue
        state = str(item.get("state") or "unknown")
        factor = {"free": 1.0, "slow": 1.15, "heavy": 1.3, "stopped": 1.8, "closed": 2.0, "hazard": 1.45}.get(state, 1.0)
        multiplier = max(multiplier, factor)
        if rank.get(state, 0) > rank[strongest]:
            strongest = state
        matched_obs.append(item)

    authority = any(bool(item.get("authority_verified")) for item in matched)
    fresh_evidence = bool(matched or matched_obs)
    base_duration = float(route_v.get("duration_s") or 0)
    adjusted = round(base_duration * multiplier, 1) if base_duration else 0.0
    return {
        "state": strongest if fresh_evidence else "unknown",
        "evidence_present": fresh_evidence,
        "authority_evidence_present": authority,
        "report_count": len(matched),
        "observation_count": len(matched_obs),
        "reports": matched[:20],
        "observations": matched_obs[:20],
        "eta_multiplier": round(multiplier, 2),
        "base_duration_s": round(base_duration, 1),
        "adjusted_duration_s": adjusted,
        "reroute_recommended": strongest in {"closed", "stopped", "hazard"},
        "continuous_speed_coverage_proven": False,
        "live_claim_allowed": fresh_evidence,
        "generated_at": _now().isoformat().replace("+00:00", "Z"),
    }


def status() -> dict[str, object]:
    live = map_live_pattern.status()
    with _LOCK:
        _prune(_now())
        count = len(_OBSERVATIONS)
    return {
        "component": "OAP Live Road Intelligence",
        "observation_collector_ready": True,
        "road_state_aggregator_ready": True,
        "authority_disruption_adapter_ready": True,
        "dynamic_eta_ready": True,
        "traffic_layer_ready": True,
        "reroute_signal_ready": True,
        "authority_feed_verified": bool(live.get("authority_verified_feed")),
        "fresh_observation_count": count,
        "continuous_speed_coverage_proven": False,
        "uk_wide_live_traffic_proven": False,
        "vehicle_telemetry_integration_proven": False,
        "precise_device_location_stored": False,
        "hidden_tracking": False,
        "truth_gated": True,
    }
