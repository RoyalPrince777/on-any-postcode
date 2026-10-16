"""Canonical SMI evidence gate.

This module binds source attribution, evidence references, truth class, freshness,
contradictions and authority into one fail-closed assessment. It does not grant
execution authority or replace domain-specific observation validation.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from . import world_observation

TRUTH_CLASSES: tuple[str, ...] = (
    "observed",
    "reported",
    "inferred",
    "modelled",
    "forecast",
    "predicted",
    "hypothesised",
    "confirmed",
    "unknown",
)

AUTHORITY_STATES: tuple[str, ...] = (
    "analysis_only",
    "user_authorised",
    "operator_authorised",
    "regulator_authorised",
    "physical_control_authorised",
)


def _clean(value: object) -> str:
    return " ".join(str(value or "").strip().split())


def _clean_many(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        value = (value,)
    return tuple(dict.fromkeys(_clean(item) for item in value if _clean(item)))


def _confidence(value: object) -> int:
    try:
        score = int(value if value is not None else 0)
    except (TypeError, ValueError) as exc:
        raise ValueError("confidence must be an integer from 0 to 100") from exc
    if not 0 <= score <= 100:
        raise ValueError("confidence must be between 0 and 100")
    return score


def assess(signals: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Return one evidence-bound assessment for supplied SMI signals."""

    items = tuple(signals)
    if not items:
        raise ValueError("At least one evidence-bearing signal is required")

    records: list[dict[str, Any]] = []
    provenance: list[dict[str, str]] = []
    contradictions: list[str] = []

    for index, signal in enumerate(items):
        if not isinstance(signal, Mapping):
            raise TypeError("evidence signals must be objects")

        source = _clean(signal.get("source"))
        if not source:
            raise ValueError("evidence signal source is required")

        evidence = _clean_many(signal.get("evidence"))
        if not evidence:
            raise ValueError("evidence references are required")

        truth_class = _clean(signal.get("truth_state") or signal.get("truth_class")).lower()
        if truth_class not in TRUTH_CLASSES:
            raise ValueError(f"Unsupported truth class: {truth_class or 'missing'}")

        authority = _clean(signal.get("authority") or "analysis_only").lower()
        if authority not in AUTHORITY_STATES:
            raise ValueError(f"Unsupported authority state: {authority}")

        signal_contradictions = _clean_many(signal.get("contradictions"))
        contradictions.extend(signal_contradictions)

        raw_observation = signal.get("observation")
        observation = (
            world_observation.normalise(raw_observation)
            if raw_observation is not None
            else None
        )

        record_id = _clean(signal.get("id") or signal.get("signal_id") or f"signal-{index + 1}")
        for reference in evidence:
            provenance.append(
                {
                    "record_id": record_id,
                    "source": source,
                    "reference": reference,
                }
            )

        records.append(
            {
                "record_id": record_id,
                "source": source,
                "truth_class": truth_class,
                "confidence": _confidence(signal.get("confidence", 0)),
                "authority": authority,
                "evidence": evidence,
                "contradictions": signal_contradictions,
                "observation": observation,
            }
        )

    observed_records = tuple(
        record for record in records if record["observation"] is not None
    )
    stale_or_expired = tuple(
        record["record_id"]
        for record in observed_records
        if record["observation"]["freshness_state"] in {"stale", "expired", "unknown"}
    )
    live_claim_blocked = tuple(
        record["record_id"]
        for record in observed_records
        if not record["observation"]["live_claim_allowed"]
    )
    contradiction_set = tuple(dict.fromkeys(contradictions))

    gates = {
        "provenance": bool(provenance),
        "truth_class": all(record["truth_class"] in TRUTH_CLASSES for record in records),
        "freshness": not stale_or_expired,
        "authority": all(record["authority"] in AUTHORITY_STATES for record in records),
        "contradiction_check": not contradiction_set,
        "runtime_observation": not live_claim_blocked,
    }

    evidence_complete = all(
        gates[name]
        for name in ("provenance", "truth_class", "freshness", "authority")
    )
    consequential_green_allowed = bool(
        evidence_complete
        and gates["contradiction_check"]
        and gates["runtime_observation"]
        and all(record["authority"] != "analysis_only" for record in records)
    )

    return {
        "kind": "smi_evidence_assessment",
        "record_count": len(records),
        "records": tuple(records),
        "provenance": tuple(provenance),
        "contradictions": contradiction_set,
        "stale_or_expired_record_ids": stale_or_expired,
        "live_claim_blocked_record_ids": live_claim_blocked,
        "gates": gates,
        "evidence_complete": evidence_complete,
        "consequential_green_allowed": consequential_green_allowed,
        "execution_granted": False,
        "human_authority_final": True,
        "truth_boundary": (
            "Evidence completeness does not itself grant execution authority. "
            "Contradictions, stale observations or analysis-only authority fail closed "
            "for consequential Green."
        ),
    }


def status() -> dict[str, Any]:
    return {
        "name": "SMI Evidence Gate",
        "truth_classes": TRUTH_CLASSES,
        "authority_states": AUTHORITY_STATES,
        "required_gates": (
            "provenance",
            "truth_class",
            "freshness",
            "authority",
            "contradiction_check",
            "runtime_observation",
        ),
        "execution_granted": False,
        "human_authority_final": True,
    }
