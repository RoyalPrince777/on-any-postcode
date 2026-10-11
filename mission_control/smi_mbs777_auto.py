"""Fail-closed MBS 777 per-agent promotion advice; no autonomous authority changes."""
from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Mapping

from mission_control.hrm_agent_lifecycle import BODY_7, MIND_7, SOUL_7

PROMOTION_THRESHOLD = 97.3
GREEN_THRESHOLD = 93.0
RECOVERY_TARGET_SECONDS = 21
IMPROVEMENT_TARGET_SECONDS = 21


@dataclass(frozen=True)
class UnifiedAgentDecision:
    agent_id: str
    status: str
    promotion_eligible: bool
    recommendation: str
    missing: tuple[str, ...]
    automatic_rank_change_allowed: bool = False
    human_authority_required_for_promotion: bool = True


def evaluate_agent(
    agent_id: str,
    *,
    score: float | None,
    evidence: Mapping[str, bool],
    verified_assignments: int = 0,
    critical_violation: bool = False,
) -> UnifiedAgentDecision:
    """One agent, three inseparable planes, 21 checks, one recommendation.

    The 21-second windows are targets for recovery/verification, not timers that
    automatically claim completion, terminate agents or change permissions.
    """
    agent = str(agent_id).strip()
    if not agent:
        raise ValueError("agent_id_required")
    checks = tuple(f"{plane}.{name}" for plane, names in (
        ("MIND", MIND_7), ("BODY", BODY_7), ("SOUL", SOUL_7)
    ) for name in names)
    missing = tuple(check for check in checks if evidence.get(check) is not True)
    if critical_violation:
        return UnifiedAgentDecision(agent, "RED", False, "CONTAIN_AND_HUMAN_REVIEW", missing)
    if score is None or not isfinite(float(score)) or missing:
        return UnifiedAgentDecision(agent, "UNVERIFIED", False, "COLLECT_REAL_EVIDENCE", missing)
    value = float(score)
    if not 0 <= value <= 100:
        raise ValueError("score_out_of_range")
    if value < GREEN_THRESHOLD:
        return UnifiedAgentDecision(agent, "YELLOW", False, "RECOVER_AND_VERIFY", missing)
    if value < PROMOTION_THRESHOLD:
        return UnifiedAgentDecision(agent, "GREEN", False, "MAINTAIN", missing)
    if verified_assignments < 3:
        return UnifiedAgentDecision(agent, "GREEN", False, "VERIFY_THREE_ASSIGNMENTS", missing)
    return UnifiedAgentDecision(agent, "GREEN", True, "PROMOTION_REVIEW", missing)
