"""Review-only, first-party Raffles Mind. No legal verdicts or execution rights.

This is a domain evidence triage layer, not another Matrix or approval engine.
Jurisdiction and promotion type are claims requiring independent legal review.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum


class Triage(str, Enum):
    REQUEST_EVIDENCE = "REQUEST_EVIDENCE"
    BLOCK = "BLOCK"
    ESCALATE = "ESCALATE_TO_CANONICAL_MATRIX_REVIEW"

TERRITORIES = frozenset({"uk", "global"})
KINDS = frozenset({"free_draw", "paid_skill", "dual_route", "property_prize",
                   "community_reward"})
REQUIRED = ("sponsor_authority", "prize_authority", "fulfilment",
            "promotion_terms", "jurisdiction_review", "privacy_review")
PAID_KINDS = frozenset({"paid_skill", "dual_route"})
HIGH_VALUE_KINDS = frozenset({"property_prize"})

@dataclass(frozen=True)
class MindResult:
    decision: Triage
    reasons: tuple[str, ...]
    missing: tuple[str, ...]
    territory: str
    kind: str
    execution_granted: bool = False
    evidence_verified: bool = False
    founder_approved: bool = False
    actual_matrix_votes: tuple[str, ...] = ()


def assess(*, territory: str, kind: str,
           evidence: Mapping[str, str] | None = None,
           sponsor_funded: bool = False,
           cash_required: bool = False) -> MindResult:
    """Fail closed, never promote evidence strings into certified facts."""
    territory = str(territory or "").strip().lower()
    kind = str(kind or "").strip().lower()
    supplied = evidence if isinstance(evidence, Mapping) else {}
    missing = tuple(key for key in REQUIRED if not isinstance(
        supplied.get(key), str) or not supplied[key].strip())
    reasons = []
    if territory not in TERRITORIES:
        reasons.append("unsupported_territory")
    if kind not in KINDS:
        reasons.append("unsupported_promotion_type")
    if cash_required:
        reasons.append("zero_capital_requirement_violated")
    if kind in PAID_KINDS:
        reasons.append("paid_model_requires_separate_authorisation")
    if kind in HIGH_VALUE_KINDS:
        reasons.append("property_title_transfer_and_tax_review_required")
    if territory == "global":
        reasons.append("country_specific_eligibility_review_required")
    if not sponsor_funded:
        reasons.append("sponsor_funding_unconfirmed")
    if reasons:
        decision = Triage.BLOCK
    elif missing:
        decision = Triage.REQUEST_EVIDENCE
    else:
        decision = Triage.ESCALATE
    return MindResult(decision, tuple(reasons), missing, territory, kind)
