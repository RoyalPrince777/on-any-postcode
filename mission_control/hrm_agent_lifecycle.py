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



class AgentRank(str, Enum):
    TRAINEE = "TRAINEE"
    SPECIALIST = "SPECIALIST"
    SENIOR = "SENIOR"
    ELITE = "ELITE"
    CAPTAIN = "CAPTAIN"


RANK_ORDER: tuple[AgentRank, ...] = (
    AgentRank.TRAINEE,
    AgentRank.SPECIALIST,
    AgentRank.SENIOR,
    AgentRank.ELITE,
    AgentRank.CAPTAIN,
)

RANK_MINIMUM_STRENGTH: dict[AgentRank, float] = {
    AgentRank.TRAINEE: 0.0,
    AgentRank.SPECIALIST: 68.0,
    AgentRank.SENIOR: 78.0,
    AgentRank.ELITE: 88.0,
    AgentRank.CAPTAIN: 95.0,
}

TRAINING_25_8: dict[str, object] = {
    "name": "25-8 Training",
    "mode": "continuous_event_driven_learning",
    "literal_time_claim": False,
    "meaning": (
        "OAP shorthand for always-ready bounded learning. Training runs from real "
        "mission receipts, failures, corrections, simulations and helper reviews; "
        "it does not claim a literal 25-hour day or 8-day week."
    ),
    "production_execution_granted": False,
    "self_promotion_allowed": False,
    "self_termination_allowed": False,
    "first_party_only": True,
}


def rank_for_strength(score: float) -> AgentRank:
    """Map proven strength to a rank without granting authority."""
    clean = max(0.0, min(100.0, float(score)))
    if clean >= RANK_MINIMUM_STRENGTH[AgentRank.CAPTAIN]:
        return AgentRank.CAPTAIN
    if clean >= RANK_MINIMUM_STRENGTH[AgentRank.ELITE]:
        return AgentRank.ELITE
    if clean >= RANK_MINIMUM_STRENGTH[AgentRank.SENIOR]:
        return AgentRank.SENIOR
    if clean >= RANK_MINIMUM_STRENGTH[AgentRank.SPECIALIST]:
        return AgentRank.SPECIALIST
    return AgentRank.TRAINEE


def lifecycle_plan(
    score: float | None,
    *,
    evidence_coverage_percent: float = 0.0,
    current_rank: AgentRank | str = AgentRank.TRAINEE,
    risk: str = "low",
    material_failures: int = 0,
    helper_available: bool = True,
    termination_requested: bool = False,
) -> dict[str, object]:
    """Recommend rank/lifecycle movement from proven first-party evidence only."""

    try:
        rank = current_rank if isinstance(current_rank, AgentRank) else AgentRank(str(current_rank))
    except ValueError as exc:
        raise ValueError("invalid_agent_rank") from exc

    coverage = max(0.0, min(100.0, float(evidence_coverage_percent)))
    failures = max(0, int(material_failures))
    risk_level = str(risk).strip().lower()

    if score is None or coverage < 100.0:
        return {
            "current_rank": rank.value,
            "recommended_rank": rank.value,
            "direction": LifecycleDirection.LEARN.value,
            "promotion_candidate": False,
            "downgrade_candidate": False,
            "suspension_candidate": False,
            "termination_candidate": False,
            "helper_review_recommended": bool(helper_available),
            "training": TRAINING_25_8,
            "reason": "full_first_party_strength_evidence_required",
            "human_authority_required": False,
            "automatic_rank_change_allowed": False,
        }

    clean_score = max(0.0, min(100.0, float(score)))
    target = rank_for_strength(clean_score)
    rank_index = RANK_ORDER.index(rank)
    target_index = RANK_ORDER.index(target)
    severe_risk = risk_level in {"high", "critical", "severe"}

    if termination_requested:
        direction = LifecycleDirection.TERMINATE_CANDIDATE
        recommended = rank
    elif severe_risk or failures >= 3:
        direction = LifecycleDirection.SUSPEND
        recommended = rank
    elif target_index > rank_index:
        direction = LifecycleDirection.PROMOTE
        recommended = RANK_ORDER[rank_index + 1]
    elif target_index < rank_index:
        direction = LifecycleDirection.DOWNGRADE
        recommended = RANK_ORDER[rank_index - 1]
    elif failures > 0:
        direction = LifecycleDirection.RECOVER
        recommended = rank
    elif clean_score >= 88:
        direction = LifecycleDirection.UPGRADE
        recommended = rank
    else:
        direction = LifecycleDirection.MAINTAIN
        recommended = rank

    authority_change = direction in {
        LifecycleDirection.PROMOTE,
        LifecycleDirection.DOWNGRADE,
        LifecycleDirection.TERMINATE_CANDIDATE,
    }
    return {
        "current_rank": rank.value,
        "recommended_rank": recommended.value,
        "direction": direction.value,
        "promotion_candidate": direction is LifecycleDirection.PROMOTE,
        "downgrade_candidate": direction is LifecycleDirection.DOWNGRADE,
        "suspension_candidate": direction is LifecycleDirection.SUSPEND,
        "termination_candidate": direction is LifecycleDirection.TERMINATE_CANDIDATE,
        "helper_review_recommended": bool(
            helper_available
            and direction
            in {
                LifecycleDirection.LEARN,
                LifecycleDirection.RECOVER,
                LifecycleDirection.DOWNGRADE,
                LifecycleDirection.SUSPEND,
            }
        ),
        "training": TRAINING_25_8,
        "reason": "first_party_strength_and_risk_review",
        "human_authority_required": authority_change,
        "automatic_rank_change_allowed": False,
    }


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
