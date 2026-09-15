"""Governed HRM agent lifecycle and canonical 7-7-7 policy.

Policy only: this module does not grant permissions, deploy, terminate, or
promote agents. Human Authority remains final for governed authority changes.
Safety containment may fail closed while awaiting review.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ReviewDepth(Enum):
    """Legacy compatibility depth. New governance is expressed through 7-7-7."""

    QUICK = 3
    COUNCIL = 7
    FULL = 21


class GovernancePlane(str, Enum):
    MIND = "MIND"
    BODY = "BODY"
    SOUL = "SOUL"


MIND_7 = (
    "evidence",
    "context",
    "intelligence",
    "confidence",
    "dependencies",
    "alternatives",
    "judgement",
)

BODY_7 = (
    "capability",
    "permissions",
    "tools",
    "execution",
    "verification",
    "performance",
    "receipt",
)

SOUL_7 = (
    "purpose",
    "human_benefit",
    "consent",
    "integrity",
    "culture",
    "guardian_safety",
    "human_authority",
)

GOVERNANCE_777 = {
    GovernancePlane.MIND: MIND_7,
    GovernancePlane.BODY: BODY_7,
    GovernancePlane.SOUL: SOUL_7,
}

CANONICAL_GOVERNANCE = "7-7-7"
TOTAL_GOVERNED_CHECKS = sum(len(checks) for checks in GOVERNANCE_777.values())


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
    """Compatibility selector; risk always overrides speed."""
    risk = str(risk).strip().lower()
    if authority_change or risk in {"high", "critical", "severe"}:
        return ReviewDepth.FULL
    if risk in {"medium", "elevated"}:
        return ReviewDepth.COUNCIL
    return ReviewDepth.QUICK


def governance_checks(*, risk: str = "low", authority_change: bool = False) -> dict[GovernancePlane, tuple[str, ...]]:
    """Return the canonical 7-7-7 checks.

    All three planes remain represented for every governed Signal. Runtime may
    optimise how evidence is gathered, but it may not silently remove a plane.
    High-risk and authority-changing work must fail closed if required proof is
    unavailable.
    """
    _ = required_depth(risk=risk, authority_change=authority_change)
    return GOVERNANCE_777


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


# Compatibility surface for existing callers while 7-7-7 becomes canonical.
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
    ReviewDepth.FULL: MIND_7 + BODY_7 + SOUL_7,
}

# Legacy timing targets are retained only for compatibility; 7-7-7 is not a
# forced deadline model.
TARGET_SECONDS = {ReviewDepth.QUICK: 3, ReviewDepth.COUNCIL: 7, ReviewDepth.FULL: 21}

assert TOTAL_GOVERNED_CHECKS == 21
