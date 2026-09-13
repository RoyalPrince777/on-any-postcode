"""Governed cross-system Ecosystem Intelligence for OAP.

This layer correlates bounded signals across OAP systems and places so SMI can
understand whole-environment pressure, opportunity and second-order effects.
It does not execute, self-approve, create agents, change permissions, or bypass
Guardian, Green Gate, War Room or Human Authority.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from . import matrix_signal_bus, workspaces

ECOSYSTEM_DOMAINS: tuple[str, ...] = (
    "people",
    "place",
    "movement",
    "economy",
    "culture",
    "nature",
    "infrastructure",
    "trust",
    "opportunity",
    "risk",
)

TIME_HORIZONS: tuple[str, ...] = ("now", "next", "trend")
TRUTH_STATES: tuple[str, ...] = ("observed", "inferred", "forecast", "confirmed")
PRESSURE_DIMENSIONS: tuple[str, ...] = (
    "demand",
    "infrastructure",
    "movement",
    "trust",
    "economic",
    "environmental",
    "cultural_energy",
    "opportunity_strength",
    "recovery_capacity",
)

ECOSYSTEM_LAW: tuple[str, ...] = (
    "Nothing important is judged in isolation.",
    "Every signal is interpreted by its effect on the wider ecosystem.",
    "Observed, inferred, forecast and confirmed states remain distinct.",
    "Aggregate contextual intelligence is preferred over unnecessary personal tracking.",
    "Ecosystem Intelligence recommends; it does not execute.",
    "SMI interprets; Guardian protects; HRM remembers; Human Authority decides.",
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def status() -> dict[str, Any]:
    """Return the bounded Ecosystem Intelligence contract."""

    workspace = workspaces.get("ecosystem")
    return {
        "name": "OAP Ecosystem Intelligence",
        "mode": "cross_system_contextual_reasoning",
        "timestamp_utc": _now(),
        "workspace": workspace,
        "domains": ECOSYSTEM_DOMAINS,
        "time_horizons": TIME_HORIZONS,
        "truth_states": TRUTH_STATES,
        "pressure_dimensions": PRESSURE_DIMENSIONS,
        "law": ECOSYSTEM_LAW,
        "matrix_system": "required",
        "matrix_signal_bus": "required",
        "smi_review": "required",
        "hrm_learning": "required_for_outcomes",
        "guardian": "required",
        "green_gate": "required",
        "war_room": "required_for_consequential_decisions",
        "human_authority": "final",
        "execution_granted": False,
        "self_approval_allowed": False,
        "automatic_deploy_allowed": False,
        "full_green": False,
    }


def _score(value: object, name: str) -> int:
    try:
        score = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be an integer from 0 to 100") from exc
    if not 0 <= score <= 100:
        raise ValueError(f"{name} must be between 0 and 100")
    return score


def _normalise_signal(signal: Mapping[str, Any]) -> dict[str, Any]:
    domain = str(signal.get("domain") or "").strip().lower()
    if domain not in ECOSYSTEM_DOMAINS:
        raise ValueError(f"Unsupported ecosystem domain: {domain or 'missing'}")

    horizon = str(signal.get("horizon") or "now").strip().lower()
    if horizon not in TIME_HORIZONS:
        raise ValueError(f"Unsupported ecosystem horizon: {horizon}")

    truth_state = str(signal.get("truth_state") or "observed").strip().lower()
    if truth_state not in TRUTH_STATES:
        raise ValueError(f"Unsupported truth state: {truth_state}")

    summary = str(signal.get("summary") or "").strip()
    if not summary:
        raise ValueError("Ecosystem signal summary is required")

    place = str(signal.get("place") or "").strip()
    source = str(signal.get("source") or "").strip()
    evidence = tuple(
        dict.fromkeys(
            str(item).strip()
            for item in (signal.get("evidence") or ())
            if str(item).strip()
        )
    )
    pressure = _score(signal.get("pressure", 0), "pressure")
    confidence = _score(signal.get("confidence", 50), "confidence")

    return {
        "domain": domain,
        "horizon": horizon,
        "truth_state": truth_state,
        "summary": summary,
        "place": place,
        "source": source,
        "evidence": evidence,
        "pressure": pressure,
        "confidence": confidence,
    }


def _pressure_state(average: float) -> str:
    if average >= 80:
        return "critical"
    if average >= 60:
        return "high"
    if average >= 35:
        return "rising"
    return "stable"


def analyse(
    signals: Iterable[Mapping[str, Any]],
    *,
    scope: str = "OAP World",
    pressure_scores: Mapping[str, object] | None = None,
) -> dict[str, Any]:
    """Correlate multi-domain ecosystem signals without taking action."""

    items = tuple(_normalise_signal(signal) for signal in signals)
    if not items:
        raise ValueError("At least one ecosystem signal is required")

    domains = tuple(dict.fromkeys(item["domain"] for item in items))
    places = tuple(
        dict.fromkeys(item["place"] for item in items if item["place"])
    )
    horizons = tuple(dict.fromkeys(item["horizon"] for item in items))
    average_pressure = sum(item["pressure"] for item in items) / len(items)
    strongest = min(items, key=lambda item: item["pressure"])
    weakest = max(items, key=lambda item: item["pressure"])
    consequential = average_pressure >= 60 or weakest["pressure"] >= 80

    scores: dict[str, int] = {}
    for key, value in (pressure_scores or {}).items():
        key_name = str(key).strip().lower()
        if key_name not in PRESSURE_DIMENSIONS:
            raise ValueError(f"Unsupported pressure dimension: {key_name}")
        scores[key_name] = _score(value, key_name)

    truth_mix = {
        state: sum(1 for item in items if item["truth_state"] == state)
        for state in TRUTH_STATES
    }
    cross_domain = len(domains) >= 2
    explanation = (
        f"{len(items)} signals across {len(domains)} domains indicate "
        f"{_pressure_state(average_pressure)} ecosystem pressure."
    )

    signal = matrix_signal_bus.route_signal(
        sender="Trinity",
        topic=f"Ecosystem Intelligence: {scope}",
        kind="ecosystem_intelligence",
        recipients=("SMI",),
        urgency=(
            "critical"
            if weakest["pressure"] >= 90
            else "high"
            if consequential
            else "normal"
        ),
        confidence=max(item["confidence"] for item in items) / 100,
        evidence=tuple(
            evidence
            for item in items
            for evidence in item["evidence"]
        ),
        requested_action="review_ecosystem_context",
        consequential=consequential,
    )

    return {
        "analysis_id": f"ECO-{uuid4().hex[:12].upper()}",
        "timestamp_utc": _now(),
        "scope": str(scope).strip() or "OAP World",
        "state": _pressure_state(average_pressure),
        "average_pressure": round(average_pressure, 1),
        "cross_domain": cross_domain,
        "domains": domains,
        "places": places,
        "horizons": horizons,
        "truth_mix": truth_mix,
        "pressure_scores": scores,
        "signals": items,
        "explanation": explanation,
        "strongest_link": {
            "domain": strongest["domain"],
            "summary": strongest["summary"],
            "pressure": strongest["pressure"],
        },
        "weakest_link": {
            "domain": weakest["domain"],
            "summary": weakest["summary"],
            "pressure": weakest["pressure"],
        },
        "matrix_signal": signal,
        "smi_review_required": True,
        "guardian_required": True,
        "green_gate_required": True,
        "war_room_required": consequential,
        "human_authority_required": consequential,
        "recursive_self_improvement_candidate": (
            cross_domain and consequential
        ),
        "execution_granted": False,
        "external_action_taken": False,
        "self_approval_allowed": False,
        "automatic_deploy_allowed": False,
        "full_green": False,
    }
