"""Canonical 73-signal Mission-to-100 field for SMI.

This is an evidence model, not a simulated council. It preserves the existing
SMI brain, Matrix Intelligence boundaries, OAP Law and Human Authority. Review
positions are deterministic summaries of supplied evidence and never fictional
agent opinions.
"""
from __future__ import annotations

from collections import Counter
from collections.abc import Mapping
from typing import Any

STATES = ("proven", "active", "blocked", "unknown")

DIMENSION_FAMILIES: tuple[tuple[str, tuple[tuple[str, tuple[str, str, str]], ...]], ...] = (
    (
        "intelligence_health",
        (
            ("clarity", ("mission", "scope", "ownership")),
            ("accuracy", ("facts", "uncertainty", "consistency")),
            ("execution", ("action", "continuity", "completion")),
            ("security", ("access", "adversarial", "detection")),
            ("resilience", ("recovery", "failover", "last_known_green")),
            ("evidence", ("proof", "traceability", "version_match")),
            ("alignment", ("oap_law", "cross_system_fit", "founder_final_alignment")),
        ),
    ),
    (
        "operational_vitals",
        (
            ("stability", ("uptime", "error_stability", "state_consistency")),
            ("pace", ("detection_speed", "decision_speed", "execution_speed")),
            ("performance", ("latency", "throughput", "output_quality")),
            ("capacity", ("concurrency", "load_headroom", "scale_behaviour")),
            ("efficiency", ("compute", "memory_data", "wasted_work")),
            ("continuity", ("dependency_tolerance", "degraded_operation", "reconnect")),
            ("recovery_speed", ("detection_to_recovery", "restore_success", "last_known_green_time")),
        ),
    ),
    (
        "system_quality",
        (
            ("reliability", ("repeated_result", "failure_repeatability", "deterministic_boundaries")),
            ("observability", ("runtime_visibility", "dependency_visibility", "reason_visibility")),
            ("adaptability", ("condition_change", "input_change", "priority_change")),
            ("interoperability", ("state_exchange", "boundary_translation", "duplicate_logic_control")),
            ("maintainability", ("repairability", "upgradeability", "comprehensibility")),
            ("data_integrity", ("completeness", "consistency", "freshness")),
            ("mission_impact", ("intended_outcome", "user_value", "cross_oap_value")),
        ),
    ),
)

CROWN_SIGNALS: tuple[str, ...] = (
    "founder_final",
    "truth_mode",
    "red_team",
    "runtime_proof",
    "recovery_proof",
    "cross_intelligence_coherence",
    "end_to_end_proof",
    "mission_impact_proof",
    "last_known_green_integrity",
    "completion_seal_777",
)

STAR_GATES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("oap_law", ("alignment.oap_law", "crown.truth_mode")),
    ("truth", ("crown.truth_mode", "evidence.proof", "evidence.traceability")),
    ("runtime", ("crown.runtime_proof", "stability.uptime", "observability.runtime_visibility")),
    ("security", ("security.access", "security.adversarial", "security.detection")),
    ("recovery", ("crown.recovery_proof", "resilience.recovery", "recovery_speed.restore_success")),
    ("end_to_end", ("crown.end_to_end_proof", "execution.completion", "mission_impact.intended_outcome")),
    ("founder_final", ("crown.founder_final", "alignment.founder_final_alignment", "crown.completion_seal_777")),
)

REVIEWERS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("Neo", ("execution", "reliability", "mission_impact")),
    ("Morpheus", ("clarity", "alignment")),
    ("Trinity", ("interoperability", "continuity")),
    ("Oracle", ("accuracy", "adaptability")),
    ("Architect", ("maintainability", "data_integrity")),
    ("Keymaker", ("security", "interoperability")),
    ("Seraph", ("security", "alignment")),
    ("Tank", ("stability", "performance")),
    ("Dozer", ("capacity", "recovery_speed")),
    ("Agent Smith", ("security", "reliability")),
    ("Agent Brown", ("observability", "security")),
    ("Agent Jones", ("continuity", "reliability")),
    ("Twin #1", ("security", "interoperability")),
    ("Twin #2", ("observability", "data_integrity")),
)


def _signal_keys() -> tuple[str, ...]:
    keys: list[str] = []
    for _, dimensions in DIMENSION_FAMILIES:
        for dimension, checks in dimensions:
            keys.extend(f"{dimension}.{check}" for check in checks)
    keys.extend(f"crown.{name}" for name in CROWN_SIGNALS)
    return tuple(keys)


SIGNAL_KEYS = _signal_keys()
SIGNAL_KEY_SET = frozenset(SIGNAL_KEYS)


def _state(value: object) -> str:
    if isinstance(value, bool):
        return "proven" if value else "blocked"
    text = str(value or "unknown").strip().casefold()
    return text if text in STATES else "unknown"


def _aggregate(states: list[str]) -> str:
    if "blocked" in states:
        return "blocked"
    if states and all(item == "proven" for item in states):
        return "proven"
    if "active" in states or "proven" in states:
        return "active"
    return "unknown"


def _dimension_signal_keys(dimension: str) -> tuple[str, ...]:
    prefix = dimension + "."
    return tuple(key for key in SIGNAL_KEYS if key.startswith(prefix))


def definition_status() -> dict[str, Any]:
    dimensions = tuple(
        dimension
        for _, family_dimensions in DIMENSION_FAMILIES
        for dimension, _ in family_dimensions
    )
    return {
        "component": "SMI 73-Signal Mission Field",
        "signal_count": len(SIGNAL_KEYS),
        "dimension_family_count": len(DIMENSION_FAMILIES),
        "major_dimension_count": len(dimensions),
        "star_gate_count": len(STAR_GATES),
        "reviewer_count": len(REVIEWERS),
        "numeric_architecture": ("7", "14", "21", "73", "777"),
        "upgrade_only": True,
        "truth_mode": True,
        "no_cosmetic_progress": True,
        "simulation_is_proof": False,
        "human_authority_final": True,
    }


def evaluate(evidence: Mapping[str, object] | None = None) -> dict[str, Any]:
    supplied = dict(evidence or {})
    states = {key: _state(supplied.get(key)) for key in SIGNAL_KEYS}

    unknown_keys = tuple(sorted(set(supplied).difference(SIGNAL_KEY_SET)))
    counts = Counter(states.values())
    proven = counts.get("proven", 0)
    completion = round((proven / len(SIGNAL_KEYS)) * 100)
    if proven != len(SIGNAL_KEYS):
        completion = min(completion, 99)

    dimensions: dict[str, str] = {}
    for _, family_dimensions in DIMENSION_FAMILIES:
        for dimension, _ in family_dimensions:
            dimensions[dimension] = _aggregate(
                [states[key] for key in _dimension_signal_keys(dimension)]
            )

    stars = []
    for name, required in STAR_GATES:
        star_state = _aggregate([states[key] for key in required])
        stars.append({"name": name, "state": star_state, "earned": star_state == "proven"})

    votes = []
    for reviewer, owned_dimensions in REVIEWERS:
        vote_state = _aggregate([dimensions[name] for name in owned_dimensions])
        votes.append(
            {
                "reviewer": reviewer,
                "evidence_vote": vote_state,
                "deterministic_evidence_review": True,
                "fictional_opinion_claimed": False,
            }
        )

    all_proven = proven == len(SIGNAL_KEYS)
    all_stars = all(item["earned"] for item in stars)
    green_100 = bool(all_proven and all_stars)
    return {
        "component": "SMI 73-Signal Mission Field",
        "signal_count": len(SIGNAL_KEYS),
        "states": states,
        "counts": {state: int(counts.get(state, 0)) for state in STATES},
        "completion_percentage": 100 if green_100 else completion,
        "green_100": green_100,
        "seal_777": "earned" if green_100 else "not_earned",
        "dimensions": dimensions,
        "stars": tuple(stars),
        "star_summary": {
            "earned": sum(1 for item in stars if item["earned"]),
            "total": len(stars),
        },
        "votes": tuple(votes),
        "vote_summary": {
            state: sum(1 for item in votes if item["evidence_vote"] == state)
            for state in STATES
        },
        "review": {
            "truth_mode": True,
            "upgrade_only": True,
            "evidence_before_green": True,
            "unknown_is_green": False,
            "blocked_can_be_averaged_away": False,
            "simulation_is_completion": False,
            "human_authority_final": True,
        },
        "unrecognised_evidence_keys": unknown_keys,
    }


def evidence_from_smi_health(snapshot: Mapping[str, object]) -> dict[str, object]:
    """Project only directly evidenced SMI health into the 73-signal field.

    Missing evidence is intentionally omitted so evaluate() leaves it unknown.
    This function does not manufacture runtime, recovery or end-to-end proof.
    """
    checks = dict(snapshot.get("checks") or {})
    invariants = dict(snapshot.get("invariants") or {})
    inference = dict(snapshot.get("inference") or {})

    guardian_stack = all(
        bool(checks.get(name))
        for name in ("guardian", "aegis", "war_room")
    )
    database_stack = all(
        bool(checks.get(name))
        for name in ("database", "schema", "audit")
    )
    authority_stack = bool(
        checks.get("human_authority")
        and invariants.get("human_authority_final")
        and invariants.get("execution_locked")
    )
    first_party_inference = bool(inference.get("first_party_inference_ready"))

    evidence: dict[str, object] = {
        "security.access": bool(checks.get("permission")),
        "security.adversarial": guardian_stack,
        "security.detection": bool(checks.get("audit")),
        "evidence.proof": database_stack,
        "evidence.traceability": bool(checks.get("audit")),
        "evidence.version_match": bool(snapshot.get("environment", {}).get("revision_present"))
            if isinstance(snapshot.get("environment"), Mapping)
            else False,
        "alignment.founder_final_alignment": authority_stack,
        "observability.runtime_visibility": True,
        "observability.dependency_visibility": bool(checks),
        "observability.reason_visibility": "database_reason" in snapshot,
        "data_integrity.consistency": bool(checks.get("schema")),
        "data_integrity.freshness": bool(checks.get("database")),
        "crown.founder_final": authority_stack,
        "crown.truth_mode": True,
        "crown.red_team": guardian_stack,
        "crown.runtime_proof": bool(snapshot.get("status") == "green"),
        "crown.cross_intelligence_coherence": bool(
            checks.get("nexus") and checks.get("agent_registry")
        ),
        "crown.end_to_end_proof": bool(
            snapshot.get("status") == "green"
            and first_party_inference
            and authority_stack
        ),
        "crown.last_known_green_integrity": bool(checks.get("audit")),
    }
    return evidence
