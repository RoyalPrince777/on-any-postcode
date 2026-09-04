"""Governed, first-party SMI thinking-process projection.

This module does not expose model chain-of-thought. It defines the observable work
stages, evidence labels and completion summary that Personal SMI may show to the
Founder while private model reasoning remains private. The process is advisory,
uses the canonical OAP signal language, and never gains execution or approval
authority.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from . import live_signals

THINKING_STAGES: tuple[dict[str, str], ...] = (
    {
        "id": "understand",
        "name": "Understand",
        "signal": "starting",
        "public_label": "Understanding the request",
        "purpose": "Identify the requested outcome and bounded task without inventing intent.",
    },
    {
        "id": "context",
        "name": "Context",
        "signal": "memory_active",
        "public_label": "Checking context and governed memory",
        "purpose": "Use supplied conversation, HRM lessons and attached media without inventing memory.",
    },
    {
        "id": "route",
        "name": "Route",
        "signal": "thinking",
        "public_label": "Routing through the SMI brain",
        "purpose": "Select the relevant task family, Intelligence domains, agents and brain regions.",
    },
    {
        "id": "evidence",
        "name": "Evidence",
        "signal": "working",
        "public_label": "Checking evidence, freshness and unknowns",
        "purpose": "Separate verified evidence, inference and unknown state; lower confidence when proof is missing.",
    },
    {
        "id": "challenge",
        "name": "Challenge",
        "signal": "synchronising",
        "public_label": "Checking risks, contradictions and alternatives",
        "purpose": "Use diagnostic, resilience, meta-intelligence and War Room review where required.",
    },
    {
        "id": "synthesise",
        "name": "Synthesise",
        "signal": "thinking",
        "public_label": "Building the clearest direct answer",
        "purpose": "Combine the strongest supported answer, uncertainty and practical next action without filler.",
    },
    {
        "id": "govern",
        "name": "Govern",
        "signal": "protected",
        "public_label": "Guardian, Judgement and HRM final checks",
        "purpose": "Preserve safety, authority, coherence, audit and memory boundaries before completion.",
    },
)

CORE_EVENT_STAGE_MAP = {
    "received": "understand",
    "identity": "context",
    "permission": "context",
    "media": "context",
    "guardian": "challenge",
    "provider": "synthesise",
    "hrm": "govern",
}


def _stage(stage_id: str) -> dict[str, str]:
    return next(item for item in THINKING_STAGES if item["id"] == stage_id)


def stage_event(stage_id: object, *, source_stage: object = "runtime") -> dict[str, Any]:
    """Return one safe observable stage event from the canonical seven-stage process."""

    requested = str(stage_id or "").strip().casefold()
    valid_ids = {item["id"] for item in THINKING_STAGES}
    resolved = requested if requested in valid_ids else "understand"
    definition = _stage(resolved)
    signal = live_signals.get_signal(definition["signal"])
    return {
        "stage": resolved,
        "stage_name": definition["name"],
        "label": f"{signal['emoji']} {definition['public_label']}",
        "summary": definition["purpose"],
        "signal": signal,
        "source_stage": str(source_stage or "runtime")[:80],
        "private_reasoning_exposed": False,
        "chain_of_thought": False,
    }


def public_stage_event(core_stage: object, fallback_label: object = "") -> dict[str, Any]:
    """Translate one low-level runtime event into a safe SMI work-stage event."""

    raw = str(core_stage or "").strip().casefold()
    stage_id = CORE_EVENT_STAGE_MAP.get(raw, "understand")
    return stage_event(stage_id, source_stage=raw or fallback_label or "runtime")


def process_contract() -> dict[str, Any]:
    """Return the canonical observable process contract."""

    return {
        "name": "SMI Thinking Process",
        "version": "1.0",
        "owner": "ON ANY POSTCODE",
        "first_party_only": True,
        "stage_count": len(THINKING_STAGES),
        "stages": tuple(
            {
                **item,
                "signal": live_signals.get_signal(item["signal"]),
            }
            for item in THINKING_STAGES
        ),
        "private_reasoning_exposed": False,
        "chain_of_thought_exposed": False,
        "safe_process_summaries": True,
        "provider_identity": False,
        "decision_authority": False,
        "execution_authority": False,
        "human_authority_final": True,
        "truth_boundary": (
            "Visible stages describe governed work and evidence state only. They do not "
            "reveal hidden model reasoning, private chain-of-thought or provider internals."
        ),
    }


def _bounded_score(value: object) -> int | None:
    try:
        score = int(round(float(value)))
    except (TypeError, ValueError):
        return None
    return min(100, max(0, score))


def completion_summary(result: Mapping[str, Any]) -> dict[str, Any]:
    """Build a safe post-response explanation from already-produced runtime evidence."""

    task_type = str(result.get("task_type") or "GENERAL")
    advisor_ids = result.get("advisor_ids")
    advisors = len(advisor_ids) if isinstance(advisor_ids, (tuple, list)) else 0
    regions = int(result.get("brain_regions") or 0)
    signal_level = str(result.get("signal_level") or "UNKNOWN")
    guardian = str(result.get("guardian") or "UNKNOWN")
    coherent = result.get("coherent") if isinstance(result.get("coherent"), Mapping) else {}
    coherence_score = _bounded_score(coherent.get("score"))
    judgement = result.get("judgement") if isinstance(result.get("judgement"), Mapping) else {}
    judgement_confidence = _bounded_score(judgement.get("confidence"))
    adaptive = result.get("adaptive") if isinstance(result.get("adaptive"), Mapping) else {}
    lessons = int(adaptive.get("hrm_lessons") or 0)
    war_room = result.get("war_room") if isinstance(result.get("war_room"), Mapping) else {}
    war_room_triggered = bool(war_room.get("triggered"))

    if guardian == "BLOCKED":
        outcome_signal = live_signals.get_signal("critical")
    elif str(result.get("output_state")) == "REVIEW_REQUIRED":
        outcome_signal = live_signals.get_signal("warning")
    else:
        outcome_signal = live_signals.get_signal("complete")

    evidence_state = "PARTIAL"
    if coherence_score is not None and coherence_score >= 80 and guardian != "BLOCKED":
        evidence_state = "SUPPORTED"
    if guardian == "BLOCKED":
        evidence_state = "BLOCKED"

    summary_lines = [
        f"Task routed as {task_type}.",
        f"Reviewed across {regions} brain region(s) with {advisors} registered advisor(s).",
        f"Guardian: {guardian}; signal: {signal_level}.",
        "War Room reviewed." if war_room_triggered else "Standard governed review path used.",
    ]
    if coherence_score is not None:
        summary_lines.append(f"Response coherence: {coherence_score}%.")
    if judgement_confidence is not None:
        summary_lines.append(f"Judgement confidence: {judgement_confidence}%.")
    summary_lines.append(f"Governed HRM lessons used: {lessons}.")
    summary_lines.append("Human Authority remains final.")

    return {
        "name": "SMI Thinking Process",
        "version": "1.0",
        "signal": outcome_signal,
        "task_type": task_type,
        "evidence_state": evidence_state,
        "coherence_score": coherence_score,
        "judgement_confidence": judgement_confidence,
        "war_room_triggered": war_room_triggered,
        "advisor_count": advisors,
        "brain_region_count": regions,
        "hrm_lessons_used": lessons,
        "public_summary": tuple(summary_lines),
        "private_reasoning_exposed": False,
        "chain_of_thought_exposed": False,
        "decision_authority": False,
        "execution_authority": False,
        "human_authority_final": True,
    }


def validate() -> dict[str, Any]:
    ids = tuple(item["id"] for item in THINKING_STAGES)
    errors: list[str] = []
    if len(ids) != 7:
        errors.append("SMI Thinking Process must contain exactly seven observable stages")
    if len(ids) != len(set(ids)):
        errors.append("SMI Thinking Process stage IDs must be unique")
    canonical_signal_ids = {signal["id"] for signal in live_signals.LIVE_SIGNALS}
    if any(item["signal"] not in canonical_signal_ids for item in THINKING_STAGES):
        errors.append("Every SMI Thinking Process stage must use a canonical OAP core signal")
    return {
        "passed": not errors,
        "errors": tuple(errors),
        "stage_count": len(ids),
        "private_reasoning_exposed": False,
        "human_authority_final": True,
    }
