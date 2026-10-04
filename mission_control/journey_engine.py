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
    return {
        "truth_state": truth,
        "source": source_value,
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


def status() -> dict[str, Any]:
    return {
        "product": "OAP Journey Engine",
        "ride_modes": list(RIDE_MODES),
        "network_transport_modes": list(NETWORK_MODES),
        "map_modes": list(MAP_MODES),
        "truth_states": list(TRUTH_STATES),
        "gateway_levels": list(GATEWAY_LEVELS),
        "scheduled_is_not_live": True,
        "predicted_is_not_observed": True,
        "execution_authorised": False,
        "payment_authorised": False,
        "human_authority_final": True,
    }
