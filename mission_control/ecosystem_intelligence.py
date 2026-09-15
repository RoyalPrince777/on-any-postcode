"""Governed whole-environment Ecosystem Intelligence for OAP.

Matrix Intelligence explains structure and dependencies. Ecosystem Intelligence
explains interaction, pressure, behaviour, balance, opportunity and second-order
effects across that structure so SMI receives one contextual picture rather than
isolated dashboard lights.

This layer reasons and recommends only. It cannot execute, self-approve, create
agents, change permissions, deploy, override specialist systems, or bypass
Guardian, Green Gate, War Room or Human Authority.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from . import matrix_signal_bus, workspaces

HIERARCHY: tuple[str, ...] = (
    "Human Authority",
    "SMI",
    "Ecosystem Intelligence",
    "Matrix System",
    "Specialist Systems",
    "Infrastructure / Data / Signals",
)

CORE_QUESTION = (
    "What is happening across OAP, why is it happening, what else will it affect, "
    "and what should we pay attention to next?"
)

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

DOMAIN_PURPOSES: dict[str, str] = {
    "people": "Aggregate participation, trust, contribution and demand without unnecessary personal tracking.",
    "place": "Postcode-to-global geographic concentration, pressure, opportunity and failure context.",
    "movement": "Travel, booking, routing, delivery, congestion, weather, events and mobility demand.",
    "economy": "Market, creator pathways, SIKA contribution, demand, supply and fulfilment without unproved regulated-finance claims.",
    "culture": "Music, sport, events, creators, local identity, language, trends and local energy.",
    "nature": "Weather, environmental alerts, green spaces, wellbeing, sustainability and local conditions.",
    "infrastructure": "Hosting, compute, databases, storage, routes, APIs, authentication, latency, capacity and recovery.",
    "trust": "Guardian, privacy, identity, moderation, youth safety, permissions, abuse and public/private boundaries.",
    "opportunity": "Meaningful openings formed when multiple signals combine across demand, place, creators, merchants or infrastructure.",
    "risk": "Compound fragility where individually healthy systems combine into ecosystem-level risk.",
}

TIME_HORIZONS: tuple[str, ...] = ("now", "next", "trend")
TRUTH_STATES: tuple[str, ...] = ("observed", "inferred", "forecast", "confirmed")
GEOGRAPHY_LEVELS: tuple[str, ...] = (
    "postcode",
    "borough_district",
    "county_region",
    "country",
    "continent",
    "global",
)

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

INTELLIGENCE_CYCLE: tuple[str, ...] = (
    "observe",
    "correlate",
    "contextualise",
    "detect_pattern",
    "measure_impact",
    "forecast",
    "identify_risk_or_opportunity",
    "explain",
    "recommend",
    "smi_review",
    "hrm_learn",
)

INTERNAL_RELATIONSHIP_MODEL: tuple[str, ...] = (
    "Entity",
    "Place",
    "Activity",
    "Signal",
    "Dependency",
    "Pressure",
    "Risk",
    "Opportunity",
    "Forecast",
    "Recommendation",
    "Evidence",
    "Decision",
    "Outcome",
    "Learning",
)

MATRIX_AGENT_ROLES: dict[str, str] = {
    "Architect": "structural dependencies",
    "Oracle": "consequences and forecast",
    "Trinity": "multi-system coordination",
    "Neo": "recovery paths",
    "Morpheus": "false assumptions and false-green challenge",
    "Keymaker": "permitted system paths",
    "Seraph": "trust, identity and boundary integrity",
}

EXTENDED_MATRIX_REVIEW_ROLES: dict[str, str] = {
    "Tank": "operational state",
    "Dozer": "infrastructure resilience",
    "Agent Smith": "corruption, duplication and adversarial patterns",
    "Twinz": "contradictory paths and competing interpretations",
}

ECOSYSTEM_LAW: tuple[str, ...] = (
    "Nothing important is judged in isolation; context comes from the ecosystem.",
    "Every signal is interpreted by its effect on the wider ecosystem.",
    "Observed, inferred, forecast and confirmed states remain distinct.",
    "Aggregate contextual intelligence is preferred over unnecessary personal tracking.",
    "Ecosystem Intelligence recommends; it does not execute or override specialist systems.",
    "SMI interprets; Guardian protects; HRM remembers; Human Authority decides.",
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _score(value: object, name: str) -> int:
    try:
        score = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be an integer from 0 to 100") from exc
    if not 0 <= score <= 100:
        raise ValueError(f"{name} must be between 0 and 100")
    return score


def _clean_strings(items: Iterable[object]) -> tuple[str, ...]:
    return tuple(
        dict.fromkeys(str(item).strip() for item in items if str(item).strip())
    )


def _normalise_geography(value: object) -> dict[str, str]:
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise TypeError("geography must be an object")
    result: dict[str, str] = {}
    for raw_key, raw_value in value.items():
        key = str(raw_key).strip().lower()
        if key not in GEOGRAPHY_LEVELS:
            raise ValueError(f"Unsupported geography level: {key}")
        text = str(raw_value or "").strip()
        if text:
            result[key] = text
    return result


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

    source = str(signal.get("source") or "").strip()
    if not source:
        raise ValueError("Ecosystem signal source is required")

    evidence = _clean_strings(signal.get("evidence") or ())
    pressure = _score(signal.get("pressure", 0), "pressure")
    confidence = _score(signal.get("confidence", 50), "confidence")
    geography = _normalise_geography(signal.get("geography"))
    legacy_place = str(signal.get("place") or "").strip()
    if legacy_place and not geography:
        geography = {"global": legacy_place}

    affected_systems = _clean_strings(signal.get("affected_systems") or ())
    recommendation = str(signal.get("recommendation") or "").strip()
    risk = str(signal.get("risk") or "").strip()
    opportunity = str(signal.get("opportunity") or "").strip()

    return {
        "domain": domain,
        "horizon": horizon,
        "truth_state": truth_state,
        "summary": summary,
        "source": source,
        "evidence": evidence,
        "pressure": pressure,
        "confidence": confidence,
        "geography": geography,
        "affected_systems": affected_systems,
        "recommendation": recommendation,
        "risk": risk,
        "opportunity": opportunity,
    }


def _pressure_state(average: float) -> str:
    if average >= 80:
        return "critical"
    if average >= 60:
        return "high"
    if average >= 35:
        return "rising"
    return "stable"


def _geography_values(items: tuple[dict[str, Any], ...]) -> dict[str, tuple[str, ...]]:
    values: dict[str, tuple[str, ...]] = {}
    for level in GEOGRAPHY_LEVELS:
        values[level] = tuple(
            dict.fromkeys(
                item["geography"][level]
                for item in items
                if level in item["geography"]
            )
        )
    return values


def cross_postcode_learning(signals: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Classify whether a repeated pattern is local or spans wider geography.

    This is evidence-bound pattern classification only. It does not infer a cause
    merely because several postcodes share a borough or region.
    """

    items = tuple(_normalise_signal(signal) for signal in signals)
    if not items:
        raise ValueError("At least one ecosystem signal is required")

    geo = _geography_values(items)
    postcode_counts = Counter(
        item["geography"].get("postcode")
        for item in items
        if item["geography"].get("postcode")
    )
    borough_counts = Counter(
        item["geography"].get("borough_district")
        for item in items
        if item["geography"].get("borough_district")
    )
    region_counts = Counter(
        item["geography"].get("county_region")
        for item in items
        if item["geography"].get("county_region")
    )

    distinct_postcodes = len(postcode_counts)
    if distinct_postcodes <= 1:
        pattern_scope = "local"
    elif borough_counts and len(borough_counts) == 1:
        pattern_scope = "borough_district"
    elif region_counts and len(region_counts) == 1:
        pattern_scope = "county_region"
    elif len(geo["country"]) == 1 and geo["country"]:
        pattern_scope = "country"
    else:
        pattern_scope = "multi_area"

    return {
        "pattern_scope": pattern_scope,
        "geography": geo,
        "distinct_postcodes": distinct_postcodes,
        "repeated_postcode_signals": {
            key: value for key, value in postcode_counts.items() if value > 1
        },
        "cross_postcode": distinct_postcodes >= 2,
        "cause_confirmed": False,
        "truth_boundary": (
            "Shared geography supports pattern detection, not causal proof. Cause must remain observed, inferred, forecast or confirmed according to evidence."
        ),
        "execution_granted": False,
    }


def _recommended_gate(state: str, consequential: bool, weakest: Mapping[str, Any]) -> str:
    if consequential:
        return (
            "SMI review → Guardian / Green Gate → War Room → Human Authority before any operational change."
        )
    if state == "rising":
        return "SMI review and gather stronger evidence before escalation."
    return f"Continue observation; strongest current concern is {weakest['domain']}."


def status() -> dict[str, Any]:
    """Return the bounded Ecosystem Intelligence constitutional contract."""

    workspace = workspaces.get("ecosystem")
    return {
        "name": "OAP Ecosystem Intelligence",
        "classification": "intelligence_system_not_agent",
        "mode": "whole_environment_contextual_reasoning",
        "timestamp_utc": _now(),
        "hierarchy": HIERARCHY,
        "core_question": CORE_QUESTION,
        "workspace": workspace,
        "domains": tuple(
            {"id": domain, "purpose": DOMAIN_PURPOSES[domain]}
            for domain in ECOSYSTEM_DOMAINS
        ),
        "time_horizons": TIME_HORIZONS,
        "truth_states": TRUTH_STATES,
        "geography_levels": GEOGRAPHY_LEVELS,
        "pressure_dimensions": PRESSURE_DIMENSIONS,
        "intelligence_cycle": INTELLIGENCE_CYCLE,
        "relationship_model": INTERNAL_RELATIONSHIP_MODEL,
        "matrix_agent_roles": MATRIX_AGENT_ROLES,
        "extended_matrix_roles": EXTENDED_MATRIX_REVIEW_ROLES,
        "extended_matrix_roles_status": "passport_review_only",
        "law": ECOSYSTEM_LAW,
        "matrix_system": "required",
        "matrix_signal_bus": "required",
        "smi_review": "required",
        "hrm_learning": "required_for_outcomes",
        "recursive_self_improvement": "candidate_handoff_only",
        "guardian": "required",
        "green_gate": "required",
        "war_room": "required_for_consequential_decisions",
        "human_authority": "final",
        "privacy_default": "aggregate_contextual_not_individual_surveillance",
        "execution_granted": False,
        "self_approval_allowed": False,
        "permission_change_allowed": False,
        "agent_creation_allowed": False,
        "automatic_deploy_allowed": False,
        "full_green": False,
    }


def analyse(
    signals: Iterable[Mapping[str, Any]],
    *,
    scope: str = "OAP World",
    pressure_scores: Mapping[str, object] | None = None,
) -> dict[str, Any]:
    """Correlate real supplied multi-domain signals without taking action."""

    items = tuple(_normalise_signal(signal) for signal in signals)
    if not items:
        raise ValueError("At least one ecosystem signal is required")

    domains = tuple(dict.fromkeys(item["domain"] for item in items))
    horizons = tuple(dict.fromkeys(item["horizon"] for item in items))
    average_pressure = sum(item["pressure"] for item in items) / len(items)
    strongest = min(items, key=lambda item: item["pressure"])
    weakest = max(items, key=lambda item: item["pressure"])
    consequential = average_pressure >= 60 or weakest["pressure"] >= 80
    state = _pressure_state(average_pressure)

    scores: dict[str, int] = {}
    for key, value in (pressure_scores or {}).items():
        key_name = str(key).strip().lower()
        if key_name not in PRESSURE_DIMENSIONS:
            raise ValueError(f"Unsupported pressure dimension: {key_name}")
        scores[key_name] = _score(value, key_name)

    truth_mix = {
        truth_state: sum(1 for item in items if item["truth_state"] == truth_state)
        for truth_state in TRUTH_STATES
    }
    cross_domain = len(domains) >= 2
    geography = _geography_values(items)
    geo_pattern = cross_postcode_learning(items)
    affected_systems = tuple(
        dict.fromkeys(
            system
            for item in items
            for system in item["affected_systems"]
        )
    )
    evidence = tuple(
        dict.fromkeys(
            proof
            for item in items
            for proof in item["evidence"]
        )
    )
    risks = _clean_strings(item["risk"] for item in items if item["risk"])
    opportunities = _clean_strings(
        item["opportunity"] for item in items if item["opportunity"]
    )
    recommendations = _clean_strings(
        item["recommendation"] for item in items if item["recommendation"]
    )
    forecasts = tuple(
        item["summary"]
        for item in items
        if item["truth_state"] == "forecast" or item["horizon"] == "next"
    )

    explanation = (
        f"{len(items)} evidence-bound signals across {len(domains)} domains indicate "
        f"{state} ecosystem pressure for {str(scope).strip() or 'OAP World'}."
    )

    matrix_signal = matrix_signal_bus.route_signal(
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
        evidence=evidence,
        requested_action="review_ecosystem_context",
        consequential=consequential,
    )

    result = {
        "analysis_id": f"ECO-{uuid4().hex[:12].upper()}",
        "timestamp_utc": _now(),
        "scope": str(scope).strip() or "OAP World",
        "state": state,
        "average_pressure": round(average_pressure, 1),
        "cross_domain": cross_domain,
        "domains": domains,
        "geography": geography,
        "geographic_pattern": geo_pattern,
        "horizons": horizons,
        "truth_mix": truth_mix,
        "pressure_scores": scores,
        "signals": items,
        "affected_systems": affected_systems,
        "evidence": evidence,
        "forecast": forecasts,
        "risks": risks,
        "opportunities": opportunities,
        "recommendations": recommendations,
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
        "matrix_signal": matrix_signal,
        "smi_review_required": True,
        "guardian_required": True,
        "green_gate_required": True,
        "war_room_required": consequential,
        "human_authority_required": consequential,
        "recursive_self_improvement_candidate": cross_domain and consequential,
        "execution_granted": False,
        "external_action_taken": False,
        "self_approval_allowed": False,
        "automatic_deploy_allowed": False,
        "full_green": False,
    }
    result["recommended_next_gate"] = _recommended_gate(state, consequential, weakest)
    result["founder_view"] = founder_view(result)
    return result


def founder_view(analysis: Mapping[str, Any]) -> dict[str, Any]:
    """Project one low-noise Founder decision pack from a completed analysis."""

    if not analysis.get("state") or not analysis.get("weakest_link"):
        raise ValueError("completed ecosystem analysis is required")

    geo = analysis.get("geography") or {}
    affected_places = tuple(
        value
        for level in GEOGRAPHY_LEVELS
        for value in tuple(geo.get(level) or ())
    )
    return {
        "state": analysis["state"],
        "why": analysis.get("explanation", ""),
        "strongest_link": analysis.get("strongest_link"),
        "weakest_link": analysis.get("weakest_link"),
        "affected_systems": tuple(analysis.get("affected_systems") or ()),
        "affected_places": tuple(dict.fromkeys(affected_places)),
        "evidence": tuple(analysis.get("evidence") or ()),
        "forecast": tuple(analysis.get("forecast") or ()),
        "risk": tuple(analysis.get("risks") or ()),
        "opportunity": tuple(analysis.get("opportunities") or ()),
        "pressure_scores": dict(analysis.get("pressure_scores") or {}),
        "truth_mix": dict(analysis.get("truth_mix") or {}),
        "recommended_next_gate": analysis.get("recommended_next_gate", "SMI review"),
        "human_authority_required": bool(analysis.get("human_authority_required")),
        "execution_granted": False,
    }


def recursive_improvement_handoff(analysis: Mapping[str, Any]) -> dict[str, Any]:
    """Create a side-effect-free candidate packet for the governed RSI layer."""

    eligible = bool(analysis.get("recursive_self_improvement_candidate"))
    return {
        "eligible": eligible,
        "analysis_id": str(analysis.get("analysis_id") or ""),
        "problem": (
            str((analysis.get("weakest_link") or {}).get("summary") or "")
            if eligible
            else ""
        ),
        "evidence": tuple(analysis.get("evidence") or ()) if eligible else (),
        "recommended_next_gate": (
            "Create a separate governed Recursive Self-Improvement proposal with tests and rollback."
            if eligible
            else "Continue ecosystem observation."
        ),
        "proposal_created": False,
        "execution_granted": False,
        "automatic_deploy_allowed": False,
        "human_authority_final": True,
    }
