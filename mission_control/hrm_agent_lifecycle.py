"""Governed HRM agent lifecycle depth and rating policy.

This module is deliberately policy-only: it does not grant permissions, deploy,
terminate, or promote agents. Major authority changes remain Human Authority
choices. Safety containment may fail closed while awaiting review.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ReviewDepth(Enum):
    QUICK = 3
    COUNCIL = 7
    FULL = 21


class LifecycleDirection(str, Enum):
    PROMOTE = "PROMOTE"
    UPGRADE = "UPGRADE"
    MAINTAIN = "MAINTAIN"
    LEARN = "LEARN"
    DOWNGRADE = "DOWNGRADE"
    SUSPEND = "SUSPEND"
    RECOVER = "RECOVER"
    TERMINATE_CANDIDATE = "TERMINATE_CANDIDATE"


@dataclass(frozen=True)
class AgentAssessment:
    score: float
    stars: int
    direction: LifecycleDirection
    depth: ReviewDepth
    human_authority_required: bool
    fail_closed: bool


def stars_for_score(score: float) -> int:
    score = max(0.0, min(100.0, float(score)))
    if score >= 95:
        return 7
    if score >= 88:
        return 6
    if score >= 78:
        return 5
    if score >= 68:
        return 4
    if score >= 55:
        return 3
    if score >= 40:
        return 2
    return 1


def required_depth(*, risk: str = "low", authority_change: bool = False) -> ReviewDepth:
    """Choose the minimum safe review depth; risk always overrides speed."""
    risk = str(risk).strip().lower()
    if authority_change or risk in {"high", "critical", "severe"}:
        return ReviewDepth.FULL
    if risk in {"medium", "elevated"}:
        return ReviewDepth.COUNCIL
    return ReviewDepth.QUICK


def assess_agent(
    score: float,
    *,
    risk: str = "low",
    promotion_candidate: bool = False,
    termination_candidate: bool = False,
) -> AgentAssessment:
    """Return a bounded recommendation; never performs an authority change."""
    score = max(0.0, min(100.0, float(score)))
    stars = stars_for_score(score)
    risk_level = str(risk).strip().lower()
    severe_risk = risk_level in {"high", "critical", "severe"}
    authority_change = promotion_candidate or termination_candidate
    depth = required_depth(risk=risk_level, authority_change=authority_change)

    if termination_candidate:
        direction = LifecycleDirection.TERMINATE_CANDIDATE
    elif severe_risk or score < 40:
        direction = LifecycleDirection.SUSPEND
    elif score < 55:
        direction = LifecycleDirection.DOWNGRADE
    elif score < 68:
        direction = LifecycleDirection.LEARN
    elif promotion_candidate and score >= 88:
        direction = LifecycleDirection.PROMOTE
    elif score >= 88:
        direction = LifecycleDirection.UPGRADE
    else:
        direction = LifecycleDirection.MAINTAIN

    return AgentAssessment(
        score=score,
        stars=stars,
        direction=direction,
        depth=depth,
        human_authority_required=direction
        in {LifecycleDirection.PROMOTE, LifecycleDirection.TERMINATE_CANDIDATE},
        fail_closed=severe_risk or direction == LifecycleDirection.SUSPEND,
    )


DEPTH_STEPS = {
    ReviewDepth.QUICK: ("signal", "evidence_score", "recommendation"),
    ReviewDepth.COUNCIL: (
        "signal",
        "hrm_history",
        "evidence",
        "risk",
        "performance",
        "review",
        "recommendation",
    ),
    ReviewDepth.FULL: (
        "signal",
        "identity",
        "hrm_history",
        "evidence",
        "measure",
        "risk",
        "mind_review",
        "body_review",
        "soul_review",
        "hrm_rule_check",
        "council_selection",
        "challenge",
        "adversarial_test",
        "evidence_judgement",
        "direction",
        "proving_gate",
        "smi_recommendation",
        "human_authority",
        "execute",
        "hrm_receipt",
        "learn_monitor",
    ),
}

# 3/7/21 are review depths and latency targets, never forced deadlines.
TARGET_SECONDS = {ReviewDepth.QUICK: 3, ReviewDepth.COUNCIL: 7, ReviewDepth.FULL: 21}
