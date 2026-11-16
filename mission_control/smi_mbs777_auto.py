"""Fail-closed MBS 777 per-agent promotion advice; no autonomous authority changes."""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from math import isfinite

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


# Founder-proposed agent health/rank display policy. Advisory only: existing
# lifecycle thresholds and permissions are unchanged until integration tests
# and independent Guardian/HRM gates approve a runtime migration.
STABLE_THRESHOLD = 97.0
CRITICAL_FLOOR = 93.7
AGENT_SIGNAL_COLOURS = {
    "UNTRAINED": "WHITE",
    "TRAINING": "PURPLE",
    "RECOVERY": "YELLOW",
    "STABLE": "BLUE",
    "PROMOTION_REVIEW": "GREEN",
    "DEMOTION_REVIEW": "ORANGE",
    "TERMINATION_REVIEW": "RED",
    "UNKNOWN": "WHITE",
}


def agent_health_review(
    *,
    score: float | None,
    trained: bool = False,
    evidence_complete: bool = False,
    critical_violation: bool = False,
    recovery_elapsed_seconds: float | None = None,
    peer_review_passed: bool = False,
) -> dict[str, object]:
    """Classify one agent without changing authority or terminating a process.

    A score of zero for a trained agent recommends termination *review*, not
    destructive action. An untrained agent has no valid score. The recovery
    deadline is one incident-wide monotonic duration, supplied by a trusted
    external monitor; this function never resets or runs a timer.
    """
    if not trained:
        signal, action = "UNTRAINED", "TRAIN_WITHOUT_EXECUTION"
    elif critical_violation:
        signal, action = "TERMINATION_REVIEW", "IMMEDIATE_CONTAINMENT"
    elif score is None or not evidence_complete:
        signal, action = "UNKNOWN", "BLOCK_PROMOTION_COLLECT_EVIDENCE"
    else:
        value = float(score)
        if not isfinite(value) or not 0 <= value <= 100:
            raise ValueError("invalid_agent_health_score")
        if value == 0:
            signal, action = "TERMINATION_REVIEW", "STOP_AFFECTED_EXECUTION_AND_REVIEW"
        elif value < CRITICAL_FLOOR:
            signal, action = "DEMOTION_REVIEW", "IMMEDIATE_CONTAINMENT_AND_PEER_REVIEW"
        elif value < STABLE_THRESHOLD:
            signal, action = "RECOVERY", "RESTRICT_AND_PEER_ASSIST"
        elif value < PROMOTION_THRESHOLD:
            signal, action = "STABLE", "MAINTAIN_AND_MONITOR"
        elif peer_review_passed:
            signal, action = "PROMOTION_REVIEW", "INDEPENDENT_GATES_AND_FOUNDER_REVIEW"
        else:
            signal, action = "STABLE", "REQUIRE_INDEPENDENT_PEER_REVIEW"
        if value < PROMOTION_THRESHOLD and recovery_elapsed_seconds is not None:
            elapsed = float(recovery_elapsed_seconds)
            if not isfinite(elapsed) or elapsed < 0:
                raise ValueError("invalid_recovery_elapsed_seconds")
            if elapsed >= RECOVERY_TARGET_SECONDS and value >= CRITICAL_FLOOR:
                signal, action = "DEMOTION_REVIEW", "SUSPEND_EXECUTION_AND_REVIEW"
    return {
        "signal": signal,
        "colour": AGENT_SIGNAL_COLOURS[signal],
        "recommendation": action,
        "peer_assistance_recommended": signal in {"RECOVERY", "DEMOTION_REVIEW", "TERMINATION_REVIEW"},
        "captain_review_only": signal not in {"STABLE", "PROMOTION_REVIEW"},
        "automatic_rank_change_allowed": False,
        "automatic_termination_allowed": False,
        "guardian_hrm_and_founder_final_required": True,
        "runtime_enforcement_verified": False,
    }
