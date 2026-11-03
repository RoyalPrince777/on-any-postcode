"""OAP MIND: bounded metacognitive evidence review for the existing Octopus role.

This module evaluates supplied OAP evidence metadata; it does not fetch, verify,
execute, grant permissions, learn autonomously, or certify production readiness.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

EvidenceKind = Literal["source", "test", "ci", "runtime", "device", "proposal"]
Verdict = Literal["INVESTIGATE", "HOLD", "REVIEW_READY"]

EVIDENCE_KINDS: frozenset[str] = frozenset(
    {"source", "test", "ci", "runtime", "device", "proposal"}
)


@dataclass(frozen=True)
class OAPEvidence:
    """An externally supplied record, not an authenticated receipt."""

    reference: str
    kind: EvidenceKind
    claim: str
    supports_claim: bool = True
    verified_receipt: bool = False


@dataclass(frozen=True)
class MindAssessment:
    claim: str
    specialist: str
    verdict: Verdict
    supporting_references: tuple[str, ...]
    contradicting_references: tuple[str, ...]
    unverified_references: tuple[str, ...]
    missing_proof: tuple[str, ...]
    confidence: str
    further_research_needed: bool
    advisory_only: bool = True
    founder_final: bool = True
    runtime_certified: bool = False


def assess_oap_evidence(
    claim: str,
    evidence: tuple[OAPEvidence, ...],
    *,
    required_kinds: tuple[EvidenceKind, ...] = ("source",),
) -> MindAssessment:
    """Review provenance and contradictions without manufacturing confidence.

    `verified_receipt` is a caller assertion and MUST be authenticated by the
    existing OAP receipt/HRM layer before calling this function. In particular,
    REVIEW_READY does not mean the claim is true or that execution is allowed.
    """
    if not isinstance(claim, str) or not claim.strip():
        raise ValueError("An explicit claim is required")
    if not required_kinds or any(kind not in EVIDENCE_KINDS for kind in required_kinds):
        raise ValueError("Required evidence kinds must be recognised and nonempty")
    if any(kind not in EVIDENCE_KINDS for kind in (item.kind for item in evidence)):
        raise ValueError("Unrecognised evidence kind")
    if any(not item.reference.strip() or not item.claim.strip() for item in evidence):
        raise ValueError("Evidence needs a reference and an explicit claim")
    if len({item.reference for item in evidence}) != len(evidence):
        raise ValueError("Duplicate evidence references")

    matching = tuple(item for item in evidence if item.claim == claim.strip())
    supports = tuple(item.reference for item in matching if item.supports_claim)
    contradicts = tuple(item.reference for item in matching if not item.supports_claim)
    unverified = tuple(item.reference for item in matching if not item.verified_receipt)
    verified_support = tuple(
        item for item in matching if item.supports_claim and item.verified_receipt
    )
    missing = tuple(
        kind for kind in dict.fromkeys(required_kinds)
        if not any(item.kind == kind for item in verified_support)
    )

    if contradicts:
        verdict: Verdict = "HOLD"
    elif missing or unverified:
        verdict = "INVESTIGATE"
    else:
        verdict = "REVIEW_READY"
    confidence = (
        "CONFLICTED" if contradicts else
        "INSUFFICIENT" if missing or unverified else
        "RECEIPTS_PRESENT_NOT_INDEPENDENTLY_VERIFIED"
    )
    return MindAssessment(
        claim=claim.strip(),
        specialist="Octopus",
        verdict=verdict,
        supporting_references=supports,
        contradicting_references=contradicts,
        unverified_references=unverified,
        missing_proof=missing,
        confidence=confidence,
        further_research_needed=verdict != "REVIEW_READY",
    )
