"""Seven Predator specialists contribute bounded, evidence-only mission assignments.

No model invocation, external sensors, tool execution, or authority grant.
"""
from __future__ import annotations

from dataclasses import dataclass

from oap.smi.predator_task_planning import propose_task

SPECIALISTS = (
    ("thia", "diagnostics"),
    ("dek", "recovery_planning"),
    ("bud", "verified_history"),
    ("kwei", "continuity"),
    ("tessa", "defensive_review"),
    ("njohrr", "authority_review"),
    ("wolf", "anomaly_tracking"),
)


@dataclass(frozen=True)
class MissionAssignment:
    specialist: str
    capability: str
    decision: str
    reason: str


def plan_mission(task: str, evidence: dict[str, str] | None) -> dict[str, object]:
    """Allocate advisory work; reject missing evidence without fabricating results."""
    if not isinstance(task, str) or not task.strip():
        return {"ready": False, "reason": "EMPTY_TASK", "assignments": ()}
    if not isinstance(evidence, dict) or not evidence or any(
        not isinstance(k, str) or not k.strip()
        or not isinstance(v, str) or not v.strip()
        for k, v in evidence.items()
    ):
        return {"ready": False, "reason": "UNVERIFIED_INPUT", "assignments": ()}
    assignments = []
    for specialist, capability in SPECIALISTS:
        if specialist in {"dek", "thia", "bud", "kwei"}:
            proposal = propose_task(specialist, task, evidence)
            decision, reason = proposal.decision, proposal.reason
        else:
            decision, reason = "HUMAN_REVIEW", "ADVISORY_ONLY_NO_TOOL_AUTHORITY"
        assignments.append(MissionAssignment(specialist, capability, decision, reason))
    return {
        "ready": False,
        "reason": "GOVERNED_REVIEW_REQUIRED",
        "assignments": tuple(assignments),
    }
