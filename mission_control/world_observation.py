"""Canonical OAP world-observation envelope.

This module gives SMI one structured, evidence-bound record shape for world-state
inputs without granting execution authority. It separates observation class,
source ownership, freshness and first-party boundaries so external data cannot
be mislabeled as an OAP-owned observation.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any

EVIDENCE_CLASSES: tuple[str, ...] = (
    "observed",
    "derived",
    "inferred",
    "unverified",
)

SOURCE_OWNERSHIP: tuple[str, ...] = (
    "oap_owned",
    "founder_approved_external",
    "external_public",
    "external_private",
    "unknown",
)

FIRST_PARTY_DIMENSIONS: tuple[str, ...] = (
    "software",
    "processing",
    "storage",
    "observation",
)

FRESHNESS_STATES: tuple[str, ...] = (
    "fresh",
    "aging",
    "stale",
    "expired",
    "unknown",
)

MAX_FUTURE_SKEW_SECONDS = 60


def _clean(value: object) -> str:
    return " ".join(str(value or "").strip().split())


def _parse_utc(value: object) -> datetime | None:
    raw = _clean(value)
    if not raw:
        return None
    candidate = raw[:-1] + "+00:00" if raw.endswith("Z") else raw
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError as exc:
        raise ValueError("observed_at must be ISO-8601") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _bounded_seconds(value: object, name: str, *, default: int) -> int:
    try:
        number = int(value if value is not None else default)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be an integer") from exc
    if number < 1:
        raise ValueError(f"{name} must be greater than zero")
    return min(number, 31_536_000)


def _freshness(
    *,
    observed_at: datetime | None,
    now: datetime,
    fresh_for_seconds: int,
    stale_after_seconds: int,
    expires_after_seconds: int,
) -> tuple[str, int | None]:
    if observed_at is None:
        return "unknown", None
    age = max(0, int((now - observed_at).total_seconds()))
    if age <= fresh_for_seconds:
        return "fresh", age
    if age < stale_after_seconds:
        return "aging", age
    if age < expires_after_seconds:
        return "stale", age
    return "expired", age


def normalise(
    observation: Mapping[str, Any],
    *,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Validate one world observation and return a safe canonical envelope."""

    if not isinstance(observation, Mapping):
        raise TypeError("observation must be an object")

    evidence_class = _clean(observation.get("evidence_class") or "unverified").lower()
    if evidence_class not in EVIDENCE_CLASSES:
        raise ValueError(f"Unsupported evidence class: {evidence_class}")

    source = _clean(observation.get("source"))
    if not source:
        raise ValueError("observation source is required")

    source_ownership = _clean(
        observation.get("source_ownership") or "unknown"
    ).lower()
    if source_ownership not in SOURCE_OWNERSHIP:
        raise ValueError(f"Unsupported source ownership: {source_ownership}")

    observed_at = _parse_utc(observation.get("observed_at"))
    received_at = _parse_utc(observation.get("received_at"))
    current = (now or datetime.now(UTC)).astimezone(UTC)
    if (
        observed_at is not None
        and (observed_at - current).total_seconds() > MAX_FUTURE_SKEW_SECONDS
    ):
        raise ValueError("observed_at is too far in the future")
    if (
        received_at is not None
        and (received_at - current).total_seconds() > MAX_FUTURE_SKEW_SECONDS
    ):
        raise ValueError("received_at is too far in the future")
    if observed_at is not None and received_at is not None and observed_at > received_at:
        raise ValueError("observed_at cannot be after received_at")

    fresh_for = _bounded_seconds(
        observation.get("fresh_for_seconds"),
        "fresh_for_seconds",
        default=60,
    )
    stale_after = _bounded_seconds(
        observation.get("stale_after_seconds"),
        "stale_after_seconds",
        default=300,
    )
    expires_after = _bounded_seconds(
        observation.get("expires_after_seconds"),
        "expires_after_seconds",
        default=3600,
    )
    if not fresh_for < stale_after < expires_after:
        raise ValueError(
            "freshness thresholds must satisfy fresh_for < stale_after < expires_after"
        )

    freshness_state, age_seconds = _freshness(
        observed_at=observed_at,
        now=current,
        fresh_for_seconds=fresh_for,
        stale_after_seconds=stale_after,
        expires_after_seconds=expires_after,
    )

    first_party_input = observation.get("first_party") or {}
    if not isinstance(first_party_input, Mapping):
        raise TypeError("first_party must be an object")
    first_party = {
        dimension: bool(first_party_input.get(dimension, False))
        for dimension in FIRST_PARTY_DIMENSIONS
    }

    if source_ownership != "oap_owned" and first_party["observation"]:
        raise ValueError(
            "external source cannot be marked as a first-party observation"
        )

    evidence = tuple(
        dict.fromkeys(
            _clean(item)
            for item in tuple(observation.get("evidence") or ())
            if _clean(item)
        )
    )
    live_claim_allowed = bool(
        freshness_state in {"fresh", "aging"}
        and evidence_class in {"observed", "derived"}
        and evidence
    )

    return {
        "object_id": _clean(observation.get("object_id")),
        "object_type": _clean(observation.get("object_type") or "unknown"),
        "event_type": _clean(observation.get("event_type") or "state"),
        "evidence_class": evidence_class,
        "source": source,
        "source_ownership": source_ownership,
        "observed_at": (
            observed_at.isoformat().replace("+00:00", "Z") if observed_at else ""
        ),
        "received_at": (
            received_at.isoformat().replace("+00:00", "Z") if received_at else ""
        ),
        "freshness_state": freshness_state,
        "age_seconds": age_seconds,
        "fresh_for_seconds": fresh_for,
        "stale_after_seconds": stale_after,
        "expires_after_seconds": expires_after,
        "evidence": evidence,
        "first_party": first_party,
        "live_claim_allowed": live_claim_allowed,
        "execution_granted": False,
        "human_authority_final": True,
    }


def status() -> dict[str, Any]:
    return {
        "name": "OAP World Observation Envelope",
        "evidence_classes": EVIDENCE_CLASSES,
        "source_ownership": SOURCE_OWNERSHIP,
        "first_party_dimensions": FIRST_PARTY_DIMENSIONS,
        "freshness_states": FRESHNESS_STATES,
        "external_source_can_claim_first_party_observation": False,
        "max_future_skew_seconds": MAX_FUTURE_SKEW_SECONDS,
        "execution_granted": False,
        "human_authority_final": True,
    }
