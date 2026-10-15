"""Immutable, read-only SMI governance decision records.

Records are descriptive audit artefacts, not execution permissions. External
storage, authenticated founder signatures and runtime integration are separate.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256

from oap.smi.organism_governance import GovernanceDecision


@dataclass(frozen=True)
class DecisionRecord:
    decision_id: str
    proposal: str
    recorded_at: str
    leadership_recommendation: str
    judicial_review_reference: str | None
    evidence_references: tuple[str, ...]
    advisory_votes: tuple[tuple[str, str], ...]
    governance_verdict: str
    founder_decision: str
    execution_status: str
    previous_record_hash: str | None
    record_hash: str


def record_decision(
    decision_id: str,
    review: GovernanceDecision,
    *,
    recorded_at: datetime,
    leadership_recommendation: str,
    judicial_review_reference: str | None = None,
    evidence_references: tuple[str, ...] = (),
    founder_decision: str = "PENDING",
    previous_record_hash: str | None = None,
) -> DecisionRecord:
    """Build a deterministic, hash-linked snapshot; never authorise execution."""
    if not decision_id.strip() or not leadership_recommendation.strip():
        raise ValueError("decision id and leadership recommendation are required")
    if recorded_at.tzinfo is None or recorded_at.utcoffset() is None:
        raise ValueError("recorded_at must have timezone information")
    if founder_decision not in ("PENDING", "APPROVED", "REJECTED"):
        raise ValueError("invalid founder decision")
    if founder_decision == "APPROVED" and review.verdict != "READY_FOR_FOUNDER_REVIEW":
        raise ValueError("blocked proposal cannot be marked approved")
    if review.independent_judicial_review and not judicial_review_reference:
        raise ValueError("independent judicial review requires a reference")
    if review.evidence_verified and not evidence_references:
        raise ValueError("verified evidence requires references")
    if any(not ref.strip() for ref in evidence_references):
        raise ValueError("blank evidence reference")
    payload = {
        "decision_id": decision_id.strip(),
        "proposal": review.proposal,
        "recorded_at": recorded_at.astimezone(UTC).isoformat(),
        "leadership_recommendation": leadership_recommendation.strip(),
        "judicial_review_reference": judicial_review_reference,
        "evidence_references": evidence_references,
        "advisory_votes": review.advisory_votes,
        "governance_verdict": review.verdict,
        "founder_decision": founder_decision,
        "execution_status": "NOT_AUTHORISED",
        "previous_record_hash": previous_record_hash,
    }
    digest = sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return DecisionRecord(**payload, record_hash=digest)
