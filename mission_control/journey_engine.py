"""Canonical first-party OAP Global Transport journey contract.

This module owns software-only multimodal journey composition. It never upgrades
scheduled data to live, never grants operator authority, and never moves money.
"""
from __future__ import annotations

from typing import Any
from uuid import uuid4

NETWORK_MODES = ("bus", "rail", "metro", "tram", "ferry", "coach")
RIDE_MODES = ("car", "e-bike")
MAP_MODES = ("walk", "bicycle")
ALL_MODES = RIDE_MODES + NETWORK_MODES + MAP_MODES

TRUTH_STATES = ("SCHEDULED", "PREDICTED", "OBSERVED")
GATEWAY_LEVELS = (
    "DATA_AVAILABLE",
    "PLANNING_AVAILABLE",
    "ACTION_AVAILABLE",
    "ACTION_AUTHORISED",
)
IMPACT_STATES = ("CLEAR", "WATCH", "PREDICTED_IMPACT", "IMPACT_CONFIRMED", "UNKNOWN")
RECOVERY_STATES = ("NOT_REQUIRED", "REPLAN_REQUIRED", "ALTERNATIVE_AVAILABLE", "BLOCKED", "UNKNOWN")
DEPENDENCY_TYPES = ("depends_on", "feeds", "connected_to", "routes_through", "affected_by", "alternative_to")
EVENT_LINEAGE_STATES = ("ACTIVE", "SUPERSEDED", "CORRECTED")


def _text(value: object, field: str, *, limit: int = 240) -> str:
    result = " ".join(str(value or "").split())
    if not result:
        raise ValueError(f"{field}_required")
    return result[:limit]


def transport_observation(
    *,
    truth_state: object,
    source: object,
    observed_at: object,
    freshness: object,
    confidence: object,
    source_id: object = "",
    source_group: object = "",
    content_hash: object = "",
) -> dict[str, Any]:
    truth = str(truth_state or "").strip().upper()
    if truth not in TRUTH_STATES:
        raise ValueError("transport_truth_state_invalid")
    source_value = _text(source, "source", limit=160)
    observed = _text(observed_at, "observed_at", limit=80)
    freshness_value = _text(freshness, "freshness", limit=40).lower()
    if freshness_value not in {"fresh", "aging", "stale", "expired", "unknown"}:
        raise ValueError("transport_freshness_invalid")
    if isinstance(confidence, bool) or not isinstance(confidence, int) or not 0 <= confidence <= 100:
        raise ValueError("transport_confidence_invalid")
    source_id_value = " ".join(str(source_id or "").split())[:160]
    source_group_value = " ".join(str(source_group or "").split())[:160]
    content_hash_value = str(content_hash or "").strip().lower()[:128]
    return {
        "truth_state": truth,
        "source": source_value,
        "source_id": source_id_value,
        "source_group": source_group_value,
        "content_hash": content_hash_value,
        "observed_at": observed,
        "freshness": freshness_value,
        "confidence": confidence,
        "live_claim_allowed": truth in {"PREDICTED", "OBSERVED"} and freshness_value in {"fresh", "aging"},
    }


def journey_leg(
    *,
    mode: object,
    origin: object,
    destination: object,
    observation: dict[str, Any],
    duration_minutes: object = None,
    cost: object = None,
    accessibility: object = "",
    disruption: object = "",
) -> dict[str, Any]:
    mode_value = str(mode or "").strip().lower()
    if mode_value not in ALL_MODES:
        raise ValueError("transport_mode_invalid")
    if not isinstance(observation, dict) or observation.get("truth_state") not in TRUTH_STATES:
        raise ValueError("transport_observation_required")
    if duration_minutes is not None and (
        isinstance(duration_minutes, bool)
        or not isinstance(duration_minutes, int)
        or duration_minutes < 0
    ):
        raise ValueError("transport_duration_invalid")
    return {
        "leg_id": str(uuid4()),
        "mode": mode_value,
        "origin": _text(origin, "origin"),
        "destination": _text(destination, "destination"),
        "duration_minutes": duration_minutes,
        "cost": cost,
        "accessibility": " ".join(str(accessibility or "").split())[:160],
        "disruption": " ".join(str(disruption or "").split())[:240],
        "observation": dict(observation),
        "execution_authorised": False,
    }


def compose_journey(
    *,
    origin: object,
    destination: object,
    legs: object,
    departure: object = "",
    arrival: object = "",
) -> dict[str, Any]:
    if not isinstance(legs, list) or not legs:
        raise ValueError("transport_legs_required")
    normalised = []
    confidences = []
    for leg in legs:
        if not isinstance(leg, dict) or str(leg.get("mode") or "") not in ALL_MODES:
            raise ValueError("transport_leg_invalid")
        observation = leg.get("observation")
        if not isinstance(observation, dict) or observation.get("truth_state") not in TRUTH_STATES:
            raise ValueError("transport_leg_observation_invalid")
        normalised.append(dict(leg))
        confidence = observation.get("confidence")
        if isinstance(confidence, int) and not isinstance(confidence, bool):
            confidences.append(confidence)

    return {
        "journey_id": str(uuid4()),
        "origin": _text(origin, "origin"),
        "destination": _text(destination, "destination"),
        "departure": str(departure or "")[:80],
        "arrival": str(arrival or "")[:80],
        "duration_minutes": sum(
            int(leg["duration_minutes"])
            for leg in normalised
            if isinstance(leg.get("duration_minutes"), int)
            and not isinstance(leg.get("duration_minutes"), bool)
        ),
        "cost": [leg.get("cost") for leg in normalised if leg.get("cost") is not None],
        "accessibility": [leg.get("accessibility") for leg in normalised if leg.get("accessibility")],
        "disruptions": [leg.get("disruption") for leg in normalised if leg.get("disruption")],
        "confidence": min(confidences) if confidences else 0,
        "legs": normalised,
        "execution_authorised": False,
        "payment_authorised": False,
        "human_authority_final": True,
    }



def disruption_event(
    *,
    event_type: object,
    affected_modes: object,
    observation: dict[str, Any],
    severity: object,
    evidence_ids: object = None,
    location: object = "",
    supersedes_event_id: object = "",
    correction_of_event_id: object = "",
) -> dict[str, Any]:
    if not isinstance(affected_modes, (list, tuple)) or not affected_modes:
        raise ValueError("transport_affected_modes_required")
    modes = []
    for item in affected_modes:
        mode = str(item or "").strip().lower()
        if mode not in ALL_MODES:
            raise ValueError("transport_mode_invalid")
        if mode not in modes:
            modes.append(mode)
    if not isinstance(observation, dict) or observation.get("truth_state") not in TRUTH_STATES:
        raise ValueError("transport_observation_required")
    if isinstance(severity, bool) or not isinstance(severity, int) or not 0 <= severity <= 100:
        raise ValueError("transport_severity_invalid")
    evidence = []
    if evidence_ids is not None:
        if not isinstance(evidence_ids, (list, tuple)):
            raise ValueError("transport_evidence_ids_invalid")
        for item in evidence_ids:
            value = str(item or "").strip()
            if not value or len(value) > 160:
                raise ValueError("transport_evidence_ids_invalid")
            if value not in evidence:
                evidence.append(value)
    return {
        "event_id": str(uuid4()),
        "event_type": _text(event_type, "event_type", limit=120),
        "affected_modes": modes,
        "location": " ".join(str(location or "").split())[:240],
        "severity": severity,
        "observation": dict(observation),
        "supersedes_event_id": str(supersedes_event_id or "").strip()[:160],
        "correction_of_event_id": str(correction_of_event_id or "").strip()[:160],
        "lineage_state": "ACTIVE",
        "evidence_ids": evidence,
        "execution_authorised": False,
    }



def independent_source_count(events: object) -> int:
    if not isinstance(events, list):
        raise TypeError("transport_events_invalid")
    identities = set()
    for event in events:
        if event.get("lineage_state") != "ACTIVE":
            continue
        if not isinstance(event, dict):
            raise TypeError("transport_event_invalid")
        observation = event.get("observation")
        if not isinstance(observation, dict):
            continue
        source_group = str(observation.get("source_group") or "").strip()
        source_id = str(observation.get("source_id") or "").strip()
        source = str(observation.get("source") or "").strip()
        identity = source_group or source_id or source
        if identity:
            identities.add(identity.casefold())
    return len(identities)


def reconcile_event_lineage(events: object) -> list[dict[str, Any]]:
    if not isinstance(events, list):
        raise TypeError("transport_events_invalid")
    by_id = {}
    result = []
    for raw in events:
        if not isinstance(raw, dict):
            raise TypeError("transport_event_invalid")
        event = dict(raw)
        event_id = str(event.get("event_id") or "")
        if not event_id or event_id in by_id:
            raise ValueError("transport_event_id_invalid")
        event["lineage_state"] = "ACTIVE"
        by_id[event_id] = event
        result.append(event)

    for event in result:
        supersedes = str(event.get("supersedes_event_id") or "")
        correction = str(event.get("correction_of_event_id") or "")
        for target_id, state in ((supersedes, "SUPERSEDED"), (correction, "CORRECTED")):
            if not target_id:
                continue
            if target_id == event["event_id"] or target_id not in by_id:
                raise ValueError("transport_event_lineage_invalid")
            by_id[target_id]["lineage_state"] = state
    return result


def contradiction_registry(events: object) -> list[dict[str, Any]]:
    reconciled = reconcile_event_lineage(events)
    active = [event for event in reconciled if event.get("lineage_state") == "ACTIVE"]
    contradictions = []
    for index, left in enumerate(active):
        for right in active[index + 1:]:
            if set(left.get("affected_modes") or []).isdisjoint(right.get("affected_modes") or []):
                continue
            left_obs = left.get("observation") or {}
            right_obs = right.get("observation") or {}
            left_truth = left_obs.get("truth_state")
            right_truth = right_obs.get("truth_state")
            left_type = str(left.get("event_type") or "").casefold()
            right_type = str(right.get("event_type") or "").casefold()
            opposite = (
                ("clear" in left_type and any(word in right_type for word in ("blocked", "suspended", "closed")))
                or ("clear" in right_type and any(word in left_type for word in ("blocked", "suspended", "closed")))
            )
            if opposite and left_truth in TRUTH_STATES and right_truth in TRUTH_STATES:
                contradictions.append({
                    "left_event_id": left.get("event_id"),
                    "right_event_id": right.get("event_id"),
                    "affected_modes": sorted(
                        set(left.get("affected_modes") or [])
                        & set(right.get("affected_modes") or [])
                    ),
                })
    return contradictions


def rank_alternatives(alternatives: object) -> list[dict[str, Any]]:
    if not isinstance(alternatives, list):
        raise TypeError("transport_alternatives_invalid")
    ranked = []
    for item in alternatives:
        if not isinstance(item, dict) or not item.get("journey_id"):
            raise ValueError("transport_alternative_invalid")
        confidence = item.get("confidence")
        duration = item.get("duration_minutes")
        if isinstance(confidence, bool) or not isinstance(confidence, int):
            confidence = 0
        if isinstance(duration, bool) or not isinstance(duration, int):
            duration = 10**9
        ranked.append(dict(item))
    ranked.sort(
        key=lambda item: (
            len(item.get("disruptions") or []),
            -int(item.get("confidence") or 0),
            int(item.get("duration_minutes") or 10**9),
            str(item.get("journey_id")),
        )
    )
    return ranked


def close_recovery_case(
    *,
    case: dict[str, Any],
    resolved_evidence_ids: object,
    operator_state_confirmed: bool,
) -> dict[str, Any]:
    if not isinstance(case, dict) or not case.get("case_id"):
        raise TypeError("transport_recovery_case_invalid")
    if not isinstance(resolved_evidence_ids, list):
        raise TypeError("transport_resolved_evidence_invalid")
    evidence = [str(item).strip() for item in resolved_evidence_ids if str(item).strip()]
    trace = case.get("evidence_trace")
    if not isinstance(trace, dict):
        raise TypeError("transport_evidence_trace_invalid")
    required = set(trace.get("evidence_ids") or [])
    provided = set(evidence)
    unresolved = list(trace.get("unresolved") or [])
    evidence_complete = required.issubset(provided) and bool(required)
    can_close = (
        case.get("recovery_state") in {"NOT_REQUIRED", "ALTERNATIVE_AVAILABLE"}
        and evidence_complete
        and operator_state_confirmed is True
        and "impact_truth_unresolved" not in unresolved
    )
    result = dict(case)
    result["resolved_evidence_ids"] = evidence
    result["operator_state_confirmed"] = operator_state_confirmed is True
    result["closed"] = can_close
    result["automatic_execution"] = False
    result["operator_action_authorised"] = False
    result["payment_action_authorised"] = False
    result["human_authority_final"] = True
    return result



def _impact_state(event: dict[str, Any]) -> str:
    observation = event.get("observation")
    if not isinstance(observation, dict):
        return "UNKNOWN"
    truth = observation.get("truth_state")
    freshness = observation.get("freshness")
    if freshness in {"stale", "expired", "unknown"}:
        return "UNKNOWN"
    if truth == "OBSERVED":
        return "IMPACT_CONFIRMED"
    if truth == "PREDICTED":
        return "PREDICTED_IMPACT"
    if truth == "SCHEDULED":
        return "WATCH"
    return "UNKNOWN"


def assess_disruptions(*, journey: dict[str, Any], events: object, dependencies: object = None) -> dict[str, Any]:
    if not isinstance(journey, dict) or not isinstance(journey.get("legs"), list):
        raise TypeError("transport_journey_invalid")
    if not isinstance(events, list):
        raise TypeError("transport_events_invalid")
    events = reconcile_event_lineage(events)
    contradictions = contradiction_registry(events)
    impacts = []
    affected_leg_ids = set()
    evidence_ids = []
    overall = "CLEAR"
    valid_leg_ids = {
        str(leg.get("leg_id"))
        for leg in journey["legs"]
        if isinstance(leg, dict) and leg.get("leg_id")
    }
    edges = []
    if dependencies is not None:
        if not isinstance(dependencies, list):
            raise ValueError("transport_dependencies_invalid")
        for edge in dependencies:
            if not isinstance(edge, dict):
                raise TypeError("transport_dependency_invalid")
            source_leg_id = str(edge.get("from_leg_id") or "")
            target_leg_id = str(edge.get("to_leg_id") or "")
            relation = str(edge.get("type") or "")
            if (
                source_leg_id not in valid_leg_ids
                or target_leg_id not in valid_leg_ids
                or source_leg_id == target_leg_id
                or relation not in DEPENDENCY_TYPES
            ):
                raise ValueError("transport_dependency_invalid")
            edges.append(
                {
                    "from_leg_id": source_leg_id,
                    "to_leg_id": target_leg_id,
                    "type": relation,
                    "evidence_id": str(edge.get("evidence_id") or "")[:160],
                }
            )

    rank = {
        "CLEAR": 0,
        "WATCH": 1,
        "PREDICTED_IMPACT": 2,
        "IMPACT_CONFIRMED": 3,
        "UNKNOWN": 4,
    }
    for event in events:
        if not isinstance(event, dict):
            raise TypeError("transport_event_invalid")
        modes = event.get("affected_modes")
        if not isinstance(modes, list):
            raise TypeError("transport_event_invalid")
        matched = [
            leg["leg_id"]
            for leg in journey["legs"]
            if isinstance(leg, dict) and leg.get("mode") in modes
        ]
        if not matched:
            continue
        direct = set(matched)
        propagated = set(matched)
        frontier = list(matched)
        visited = set(matched)
        while frontier:
            current = frontier.pop(0)
            for edge in edges:
                if edge["from_leg_id"] != current:
                    continue
                target = edge["to_leg_id"]
                if target in visited:
                    continue
                visited.add(target)
                propagated.add(target)
                frontier.append(target)
                if edge["evidence_id"] and edge["evidence_id"] not in evidence_ids:
                    evidence_ids.append(edge["evidence_id"])
        matched = sorted(propagated)
        state = _impact_state(event)
        if rank[state] > rank[overall]:
            overall = state
        affected_leg_ids.update(matched)
        for evidence_id in event.get("evidence_ids") or []:
            if evidence_id not in evidence_ids:
                evidence_ids.append(evidence_id)
        impacts.append(
            {
                "event_id": event.get("event_id"),
                "event_type": event.get("event_type"),
                "impact_state": state,
                "severity": event.get("severity"),
                "affected_leg_ids": matched,
                "direct_leg_ids": sorted(direct),
                "dependency_propagated_leg_ids": sorted(set(matched) - direct),
                "truth_state": (event.get("observation") or {}).get("truth_state"),
                "freshness": (event.get("observation") or {}).get("freshness"),
                "confidence": (event.get("observation") or {}).get("confidence"),
                "evidence_ids": list(event.get("evidence_ids") or []),
            }
        )

    return {
        "journey_id": journey.get("journey_id"),
        "impact_state": overall,
        "affected_leg_ids": sorted(affected_leg_ids),
        "impacts": impacts,
        "evidence_ids": evidence_ids,
        "independent_source_count": independent_source_count([
            event for event in events if event.get("lineage_state") == "ACTIVE"
        ]),
        "contradictions": contradictions,
        "contradiction_free": not contradictions,
        "execution_authorised": False,
        "human_authority_final": True,
    }


def recovery_plan(
    *,
    journey: dict[str, Any],
    assessment: dict[str, Any],
    alternatives: object = None,
) -> dict[str, Any]:
    if not isinstance(journey, dict) or not journey.get("journey_id"):
        raise ValueError("transport_journey_invalid")
    if not isinstance(assessment, dict) or assessment.get("journey_id") != journey.get("journey_id"):
        raise ValueError("transport_assessment_invalid")
    candidates = []
    if alternatives is not None:
        if not isinstance(alternatives, list):
            raise ValueError("transport_alternatives_invalid")
        for item in alternatives:
            if not isinstance(item, dict) or not item.get("journey_id"):
                raise ValueError("transport_alternative_invalid")
            candidates.append(dict(item))

    candidates = rank_alternatives(candidates) if candidates else []

    impact = assessment.get("impact_state")
    if impact == "CLEAR":
        state = "NOT_REQUIRED"
    elif candidates:
        state = "ALTERNATIVE_AVAILABLE"
    elif impact in {"WATCH", "PREDICTED_IMPACT", "IMPACT_CONFIRMED"}:
        state = "REPLAN_REQUIRED"
    elif impact == "UNKNOWN":
        state = "UNKNOWN"
    else:
        state = "BLOCKED"

    return {
        "journey_id": journey.get("journey_id"),
        "recovery_state": state,
        "affected_leg_ids": list(assessment.get("affected_leg_ids") or []),
        "alternative_journey_ids": [item["journey_id"] for item in candidates],
        "required_actions": (
            []
            if state == "NOT_REQUIRED"
            else ["refresh_evidence", "recalculate_journey", "confirm_operator_state"]
        ),
        "automatic_execution": False,
        "payment_action_authorised": False,
        "human_authority_final": True,
    }



def evidence_trace(
    *,
    journey: dict[str, Any],
    assessment: dict[str, Any],
    recovery: dict[str, Any],
) -> dict[str, Any]:
    journey_id = journey.get("journey_id") if isinstance(journey, dict) else None
    if (
        not journey_id
        or not isinstance(assessment, dict)
        or assessment.get("journey_id") != journey_id
        or not isinstance(recovery, dict)
        or recovery.get("journey_id") != journey_id
    ):
        raise ValueError("transport_evidence_trace_invalid")

    events = []
    for impact in assessment.get("impacts") or []:
        if not isinstance(impact, dict):
            raise TypeError("transport_impact_invalid")
        events.append(
            {
                "event_id": impact.get("event_id"),
                "event_type": impact.get("event_type"),
                "truth_state": impact.get("truth_state"),
                "freshness": impact.get("freshness"),
                "confidence": impact.get("confidence"),
                "impact_state": impact.get("impact_state"),
                "affected_leg_ids": list(impact.get("affected_leg_ids") or []),
                "evidence_ids": list(impact.get("evidence_ids") or []),
            }
        )

    unresolved = []
    if assessment.get("impact_state") == "UNKNOWN":
        unresolved.append("impact_truth_unresolved")
    if recovery.get("recovery_state") in {"UNKNOWN", "REPLAN_REQUIRED"}:
        unresolved.append("recovery_not_closed")
    if not assessment.get("evidence_ids"):
        unresolved.append("evidence_missing")
    if assessment.get("contradictions"):
        unresolved.append("contradiction_unresolved")

    return {
        "journey_id": journey_id,
        "source_events": events,
        "evidence_ids": list(assessment.get("evidence_ids") or []),
        "impact_state": assessment.get("impact_state"),
        "recovery_state": recovery.get("recovery_state"),
        "unresolved": unresolved,
        "trace_complete": not unresolved,
        "execution_authorised": False,
        "payment_authorised": False,
        "human_authority_final": True,
    }


def recovery_case(
    *,
    journey: dict[str, Any],
    assessment: dict[str, Any],
    recovery: dict[str, Any],
) -> dict[str, Any]:
    trace = evidence_trace(
        journey=journey,
        assessment=assessment,
        recovery=recovery,
    )
    state = recovery.get("recovery_state")
    if state == "NOT_REQUIRED":
        permitted = ["inspect", "evidence"]
    elif state == "ALTERNATIVE_AVAILABLE":
        permitted = ["inspect", "map", "alternatives", "evidence", "dependencies"]
    else:
        permitted = ["inspect", "map", "impact", "evidence", "dependencies"]

    return {
        "case_id": str(uuid4()),
        "journey_id": journey.get("journey_id"),
        "impact_state": assessment.get("impact_state"),
        "recovery_state": state,
        "affected_leg_ids": list(assessment.get("affected_leg_ids") or []),
        "alternative_journey_ids": list(recovery.get("alternative_journey_ids") or []),
        "evidence_trace": trace,
        "permitted_actions": permitted,
        "automatic_execution": False,
        "operator_action_authorised": False,
        "payment_action_authorised": False,
        "closed": False,
        "human_authority_final": True,
    }



def command_center_state(
    *,
    journey: dict[str, Any],
    assessment: dict[str, Any],
    recovery: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(journey, dict)
        or assessment.get("journey_id") != journey.get("journey_id")
        or recovery.get("journey_id") != journey.get("journey_id")
    ):
        raise ValueError("transport_command_center_state_invalid")
    return {
        "journey_id": journey.get("journey_id"),
        "impact_state": assessment.get("impact_state"),
        "recovery_state": recovery.get("recovery_state"),
        "affected_leg_count": len(assessment.get("affected_leg_ids") or []),
        "evidence_ids": list(assessment.get("evidence_ids") or []),
        "actions": [
            "inspect",
            "map",
            "impact",
            "alternatives",
            "evidence",
            "dependencies",
            "trace",
            "compare_time",
            "show_confidence",
            "show_source",
            "challenge",
            "recalculate",
        ],
        "execution_authorised": False,
        "payment_authorised": False,
        "human_authority_final": True,
    }



def status() -> dict[str, Any]:
    return {
        "product": "OAP Journey Engine",
        "ride_modes": list(RIDE_MODES),
        "network_transport_modes": list(NETWORK_MODES),
        "map_modes": list(MAP_MODES),
        "truth_states": list(TRUTH_STATES),
        "gateway_levels": list(GATEWAY_LEVELS),
        "dependency_types": list(DEPENDENCY_TYPES),
        "impact_states": list(IMPACT_STATES),
        "recovery_states": list(RECOVERY_STATES),
        "disruption_propagation": True,
        "dependency_propagation": True,
        "dependency_loop_protection": True,
        "alternative_recovery_contract": True,
        "evidence_lineage": True,
        "command_center_projection": True,
        "recovery_case_contract": True,
        "evidence_trace_contract": True,
        "independent_source_counting": True,
        "event_supersession": True,
        "event_correction_lineage": True,
        "contradiction_registry": True,
        "deterministic_alternative_ranking": True,
        "explicit_recovery_closure": True,
        "scheduled_is_not_live": True,
        "predicted_is_not_observed": True,
        "execution_authorised": False,
        "payment_authorised": False,
        "human_authority_final": True,
    }
