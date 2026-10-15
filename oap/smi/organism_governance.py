"""Advisory-only SMI organism governance: dimensions, review and founder gate.

This module records recommendations, not votes by running autonomous agents.
No code here authorises an action or overrides legal/security controls.
"""
from __future__ import annotations

from dataclasses import dataclass

DIMENSIONS = (
    "mind", "body", "soul", "spirit", "heart", "senses", "conscience",
    "identity", "memory", "will", "time", "growth", "recovery",
)
MASTER_VITALS = (
    "pulse", "awareness", "circulation", "integrity", "continuity",
    "energy", "balance", "adaptation", "participation", "purpose",
)
FUNCTIONS = ("leaders", "judges", "voters")
ASSIGNMENTS = {
    "leaders": ("body", "will", "time", "growth", "recovery"),
    "judges": ("conscience", "senses", "memory", "identity", "heart"),
    "voters": ("mind", "soul", "spirit"),
}


@dataclass(frozen=True)
class GovernanceDecision:
    proposal: str
    evidence_verified: bool
    independent_judicial_review: bool
    mandatory_controls_pass: bool
    advisory_votes: tuple[tuple[str, str], ...]
    verdict: str
    founder_approval_required: bool = True
    authorised: bool = False


def evaluate_governance(
    proposal: str,
    *,
    evidence_verified: bool,
    independent_judicial_review: bool,
    mandatory_controls_pass: bool,
    advisory_votes: tuple[tuple[str, str], ...] = (),
) -> GovernanceDecision:
    """Fail closed; voting cannot substitute for evidence or mandatory controls."""
    if not proposal.strip():
        raise ValueError("proposal must be nonempty")
    if any(role not in FUNCTIONS or vote not in ("SUPPORT", "OPPOSE", "ABSTAIN")
           for role, vote in advisory_votes):
        raise ValueError("unrecognised advisory vote")
    ready = all((evidence_verified, independent_judicial_review, mandatory_controls_pass))
    return GovernanceDecision(
        proposal=proposal.strip(),
        evidence_verified=evidence_verified,
        independent_judicial_review=independent_judicial_review,
        mandatory_controls_pass=mandatory_controls_pass,
        advisory_votes=advisory_votes,
        verdict="READY_FOR_FOUNDER_REVIEW" if ready else "BLOCKED",
    )
