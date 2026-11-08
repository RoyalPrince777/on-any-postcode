"""OAP Metacognitive Intelligence: bounded Octopus evidence reasoning.

Caller-provided evidence is *always* untrusted. No boolean supplied by a caller
can authenticate a source, CI outcome, device result or HRM receipt. The only
existing canonical readback integration is in oap_mind_kernel.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

# Octopus is the existing SMI systems-coordination specialist, not OAP MIND
# itself. These are design responsibilities, not independently running workers.
OCTOPUS_OPERATIONAL_ARMS: tuple[str, ...] = (
    "OBSERVE", "TRACE", "PLAN", "COORDINATE",
    "EXECUTE", "ADAPT", "RECOVER", "VERIFY",
)
OCTOPUS_PERMISSION_BOUNDARIES: tuple[str, ...] = (
    "SENSE", "READ", "ANALYSE", "INFER",
    "REMEMBER", "LEARN", "SHARE", "ACT",
)
OAP_MIND_OWNER = "SMI"
OAP_MIND_COORDINATOR = "Octopus"
OAP_MIND_SUPPORTING_ARMS: tuple[str, ...] = ("TRACE", "ADAPT", "VERIFY")

EvidenceKind = Literal["source", "test", "ci", "runtime", "device", "proposal"]
Verdict = Literal["INVESTIGATE", "HOLD", "REVIEW_READY"]

EVIDENCE_KINDS: frozenset[str] = frozenset(
    {"source", "test", "ci", "runtime", "device", "proposal"}
)


@dataclass(frozen=True)
class OAPEvidence:
    """Untrusted observation; verified_receipt is retained for compatibility ONLY."""

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
    next_evidence_action: str = "AUTHENTICATE_OAP_EVIDENCE"
    advisory_only: bool = True
    founder_final: bool = True
    runtime_certified: bool = False


def assess_oap_evidence(
    claim: str,
    evidence: tuple[OAPEvidence, ...],
    *,
    required_kinds: tuple[EvidenceKind, ...] = ("source",),
) -> MindAssessment:
    """Assess claims without promoting caller assertions into authenticated proof.

    This is an informational analysis of untrusted metadata, not Green Gate.
    A claimed verified receipt is deliberately ignored. An independent OAP
    source/CI/device or HRM readback is needed to certify actual evidence.
    """
    if not isinstance(claim, str) or not claim.strip():
        raise ValueError("An explicit claim is required")
    if not isinstance(required_kinds, tuple) or not required_kinds or any(
        kind not in EVIDENCE_KINDS for kind in required_kinds
    ):
        raise ValueError("Required evidence kinds must be recognised and nonempty")
    if not isinstance(evidence, tuple) or any(
        not isinstance(item, OAPEvidence) for item in evidence
    ):
        raise ValueError("Evidence must be a tuple of OAPEvidence")
    if any(item.kind not in EVIDENCE_KINDS for item in evidence):
        raise ValueError("Unrecognised evidence kind")
    if any(
        not isinstance(item.reference, str)
        or not item.reference.strip()
        or not isinstance(item.claim, str)
        or not item.claim.strip()
        for item in evidence
    ):
        raise ValueError("Evidence needs a reference and an explicit claim")
    if len({item.reference for item in evidence}) != len(evidence):
        raise ValueError("Duplicate evidence references")
    if any(type(item.supports_claim) is not bool for item in evidence):
        raise ValueError("Evidence support must be an explicit boolean")

    normalized_claim = claim.strip()
    matching = tuple(item for item in evidence if item.claim == normalized_claim)
    supports = tuple(item.reference for item in matching if item.supports_claim)
    contradicts = tuple(item.reference for item in matching if not item.supports_claim)

    # There is no trusted readback in this function: all metadata remains
    # unverified even when a caller sets verified_receipt=True.
    unverified = tuple(item.reference for item in evidence)
    missing = tuple(dict.fromkeys(required_kinds))
    verdict: Verdict = "HOLD" if contradicts else "INVESTIGATE"
    confidence = "CONFLICTED_UNVERIFIED" if contradicts else "UNVERIFIED"
    return MindAssessment(
        claim=normalized_claim,
        specialist="Octopus",
        verdict=verdict,
        supporting_references=supports,
        contradicting_references=contradicts,
        unverified_references=unverified,
        missing_proof=missing,
        confidence=confidence,
        further_research_needed=True,
        next_evidence_action=(
            "RESOLVE_CONTRADICTORY_OAP_RECORDS" if contradicts
            else "RETRIEVE_AND_AUTHENTICATE_OAP_PROOF"
        ),
    )


@dataclass(frozen=True)
class AgentMindReview:
    """One advisory review of another SMI role; never an agent execution record."""

    agent_name: str
    assessment: MindAssessment
    independent_review_required: bool = True
    independent_review_verified: bool = False
    permissions_granted: bool = False
    council_vote_recorded: bool = False


def assess_smi_agent_claim(
    agent_name: str,
    claim: str,
    evidence: tuple[OAPEvidence, ...],
    *,
    required_kinds: tuple[EvidenceKind, ...] = ("source",),
) -> AgentMindReview:
    """Extend OAP MIND's existing checks to named SMI specialist claims.

    Every caller record remains untrusted. Octopus may coordinate a review,
    but may not self-certify or promote agent performance. Existing Guardian,
    HRM, independent evidence and Founder Final gates remain outside this
    strictly read-only evaluator.
    """
    if not isinstance(agent_name, str) or not agent_name.strip():
        raise ValueError("An explicit SMI agent name is required")
    assessment = assess_oap_evidence(
        claim, evidence, required_kinds=required_kinds
    )
    return AgentMindReview(agent_name=agent_name.strip(), assessment=assessment)
