"""Bounded first-party Badlands task planning; no tool execution or grants."""
from __future__ import annotations

from dataclasses import dataclass

from mission_control.hrm_agent_lifecycle import lifecycle_plan
from oap.smi.predator_badlands_team import BADLANDS_TEAM

ACTIVE_CANDIDATES = frozenset({"dek", "thia", "bud", "kwei"})


@dataclass(frozen=True)
class TaskProposal:
    agent_id: str
    task: str
    responsibility: str
    decision: str
    reason: str
    lifecycle_direction: str


def propose_task(agent_id: str, task: str, evidence: dict[str, str] | None) -> TaskProposal:
    """Return advisory work allocation; unverified evidence always fails closed."""
    identity = next((item for item in BADLANDS_TEAM if item.character == agent_id), None)
    lifecycle = lifecycle_plan(None)
    direction = str(lifecycle["direction"])
    if identity is None or agent_id not in ACTIVE_CANDIDATES:
        return TaskProposal(str(agent_id), str(task), "", "DENY", "UNREGISTERED_AGENT", direction)
    if not isinstance(task, str) or not task.strip():
        return TaskProposal(agent_id, str(task), identity.responsibility, "DENY", "EMPTY_TASK", direction)
    if not isinstance(evidence, dict) or not evidence or any(
        not isinstance(k, str) or not k.strip()
        or not isinstance(v, str) or not v.strip()
        for k, v in evidence.items()
    ):
        return TaskProposal(agent_id, task, identity.responsibility, "DENY", "UNVERIFIED_INPUT", direction)
    return TaskProposal(
        agent_id, task, identity.responsibility, "HUMAN_REVIEW",
        "ADVISORY_ONLY_NO_TOOL_AUTHORITY", direction,
    )
