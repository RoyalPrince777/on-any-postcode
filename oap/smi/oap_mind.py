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


@dataclass(frozen=True)
class OctopusArmReview:
    """An arm selection proposal, never a live worker or permission grant."""

    selected_arms: tuple[str, ...]
    requested_permissions: tuple[str, ...]
    action_gate_required: bool
    advisory_only: bool = True
    authority_granted: bool = False
    runtime_verified: bool = False
    founder_final: bool = True


def review_octopus_arms(
    arms: tuple[str, ...],
    *,
    permissions: tuple[str, ...] = (),
) -> OctopusArmReview:
    """Validate an eight-arm proposal without executing or authorising it.

    Operational arm names and permission boundaries are separate namespaces.
    Merely selecting EXECUTE or requesting ACT never grants either authority.
    """
    if not isinstance(arms, tuple) or not arms or any(
        not isinstance(arm, str) or arm not in OCTOPUS_OPERATIONAL_ARMS
        for arm in arms
    ):
        raise ValueError("Specify recognised Octopus operational arms")
    if len(set(arms)) != len(arms):
        raise ValueError("Duplicate Octopus operational arms")
    if not isinstance(permissions, tuple) or any(
        not isinstance(permission, str)
        or permission not in OCTOPUS_PERMISSION_BOUNDARIES
        for permission in permissions
    ):
        raise ValueError("Specify recognised Octopus permission boundaries")
    if len(set(permissions)) != len(permissions):
        raise ValueError("Duplicate Octopus permission boundaries")
    return OctopusArmReview(
        selected_arms=arms,
        requested_permissions=permissions,
        action_gate_required=("EXECUTE" in arms or "ACT" in permissions),
    )


@dataclass(frozen=True)
class OctopusMissionReview:
    """Owner-scoped, durable mission checkpoint; no arm execution attestation."""

    mission_id: str
    mission_state: str
    selected_arms: tuple[str, ...]
    checkpoint_verified: bool
    arm_execution_status: str = "UNKNOWN"
    arm_execution_proven: bool = False
    authority_granted: bool = False
    founder_final: bool = True


def review_octopus_mission(
    *, identity_id: str, mission_id: str, arms: tuple[str, ...]
) -> OctopusMissionReview:
    """Read canonical owner-scoped mission evidence without inventing arm attribution.

    The existing ALL IN A.I. store independently checks workspace, audit and
    HRM checkpoint records. That checkpoint records mission planning/state,
    NOT which Octopus arm performed work. An unavailable or ambiguous readback
    is rejected; no execution, permission or release rights are granted.
    """
    proposal = review_octopus_arms(arms)
    if not isinstance(identity_id, str) or not identity_id.strip():
        raise ValueError("Mission identity is required")
    if not isinstance(mission_id, str) or not mission_id.strip():
        raise ValueError("Mission ID is required")
    from mission_control.all_in_ai_mission_store import read

    receipt = read(identity_id, mission_id)
    if (
        not isinstance(receipt, dict)
        or any(
            receipt.get(key) is not True
            for key in ("read_back_verified", "audit_verified", "hrm_verified")
        )
        or receipt.get("mission_id") != mission_id
        or receipt.get("state") not in ("planned", "stopped", "recovered")
        or receipt.get("execution_granted") is not False
        or receipt.get("approval_granted") is not False
        or receipt.get("human_authority_final") is not True
    ):
        raise ValueError("Canonical mission readback incomplete or mismatched")
    return OctopusMissionReview(
        mission_id=mission_id,
        mission_state=receipt["state"],
        selected_arms=proposal.selected_arms,
        checkpoint_verified=True,
    )
