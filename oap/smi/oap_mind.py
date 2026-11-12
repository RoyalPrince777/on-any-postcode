"""OAP Metacognitive Intelligence: bounded Octopus evidence reasoning.

Caller-provided evidence is *always* untrusted. No boolean supplied by a caller
can authenticate a source, CI outcome, device result or HRM receipt. The only
existing canonical readback integration is in oap_mind_kernel.
"""

from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Mapping
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


@dataclass(frozen=True)
class OctopusHandoffReview:
    """Review an existing governed handoff, not an Octopus execution receipt."""

    mission_id: str
    reviewed_request_id: str
    proposed_arm: str
    registered_action: str
    handoff_state: str
    action_authorized: bool
    arm_execution_status: str = "UNKNOWN"
    arm_attribution_verified: bool = False
    action_performed: bool = False
    authority_granted_by_octopus: bool = False
    founder_final: bool = True


def review_octopus_action_handoff(
    *, identity_id: str, mission_id: str, reviewed_request_id: str,
    proposed_arm: str, action_name: str = "SYNC_INTERNAL_RECORD",
) -> OctopusHandoffReview:
    """Inspect the canonical handoff without confusing approval and execution.

    Handoff readiness is verified by the existing action bridge and its
    owner-scoped mission/Guardian/Judgement/approval checks. The Octopus arm
    label is only a proposal. This function cannot execute the action, change
    permissions, or identify which arm actually performed it.
    """
    review_octopus_arms((proposed_arm,))
    if not all(
        isinstance(value, str) and value.strip()
        for value in (identity_id, mission_id, reviewed_request_id, action_name)
    ):
        raise ValueError("Complete handoff identifiers are required")
    from mission_control.all_in_ai_action_bridge import handoff_status

    status = handoff_status(
        identity_id, mission_id,
        reviewed_request_id=reviewed_request_id, action_name=action_name,
    )
    if (
        not isinstance(status, dict)
        or status.get("mission_id") != mission_id
        or status.get("reviewed_request_id") != reviewed_request_id
        or status.get("action_name") != action_name
        or status.get("execution_performed") is not False
        or status.get("authority_transferred") is not False
        or status.get("human_authority_final") is not True
    ):
        raise ValueError("Handoff provenance or authority mismatch")
    handoff_state = status.get("status")
    if handoff_state not in (
        "BLOCKED", "HUMAN_AUTHORITY_REQUIRED", "AUTHORIZED_NOT_EXECUTED"
    ):
        raise ValueError("Unexpected governed handoff state")
    authorised = handoff_state == "AUTHORIZED_NOT_EXECUTED"
    if status.get("execution_authorized") is not authorised:
        raise ValueError("Handoff authorization state mismatch")
    return OctopusHandoffReview(
        mission_id=mission_id,
        reviewed_request_id=reviewed_request_id,
        proposed_arm=proposed_arm,
        registered_action=action_name,
        handoff_state=handoff_state,
        action_authorized=authorised,
    )


@dataclass(frozen=True)
class OctopusA7Review:
    """A7 readiness projection, never an autonomy-level promotion."""

    ceiling: str
    proposed_arms: tuple[str, ...]
    missing_a6_proof: tuple[str, ...]
    missing_a7_proof: tuple[str, ...]
    arm_execution_attribution: str = "UNKNOWN"
    a7_enabled: bool = False
    certification_granted: bool = False
    execution_authority_granted: bool = False
    founder_final: bool = True


def review_octopus_a7_readiness(arms: tuple[str, ...]) -> OctopusA7Review:
    """Reuse the canonical A7 gate; never derive authority from a proposal.

    A8 is not a recognised SMI level. Even if the A7 evidence gate reports
    readiness, Founder certification and real arm attribution are separate.
    """
    proposal = review_octopus_arms(arms)
    from mission_control import a7_certification, autonomy_levels

    if tuple(autonomy_levels.AUTONOMY_LEVELS)[-1] != "A7":
        raise RuntimeError("Canonical autonomy ceiling changed")
    gate = a7_certification.status()
    if (
        not isinstance(gate, dict)
        or gate.get("level") != "A7"
        or gate.get("a7_enabled") is not False
        or gate.get("certification_granted") is not False
        or gate.get("execution_granted") is not False
        or gate.get("authority_moves_with_level") is not False
        or gate.get("human_authority_final") is not True
        or not isinstance(gate.get("a6_missing"), (tuple, list))
        or not isinstance(gate.get("a7_missing"), (tuple, list))
    ):
        raise RuntimeError("A7 gate returned unsafe or incomplete evidence")
    # The canonical A7 gate reports derived readiness in addition to the
    # individual missing-proof list. Reject contradictory projections rather
    # than showing a misleading Founder-ready signal.
    a6_checks = gate.get("a6_checks")
    a7_checks = gate.get("a7_checks")
    if a6_checks is not None or a7_checks is not None:
        if (
            not isinstance(a6_checks, dict)
            or not isinstance(a7_checks, dict)
            or not a6_checks
            or not a7_checks
            or any(type(value) is not bool for value in a6_checks.values())
            or any(type(value) is not bool for value in a7_checks.values())
        ):
            raise RuntimeError("A7 gate proof checks are invalid")
        missing_a6 = tuple(name for name, passed in a6_checks.items() if not passed)
        missing_a7 = tuple(name for name, passed in a7_checks.items() if not passed)
        a6_complete = not missing_a6
        a7_ready = not missing_a7 and a6_complete
        if (
            tuple(gate["a6_missing"]) != missing_a6
            or tuple(gate["a7_missing"]) != missing_a7
            or gate.get("a6_proof_complete") is not a6_complete
            or gate.get("ready_for_founder_certification") is not a7_ready
        ):
            raise RuntimeError("A7 gate readiness contradicts proof checks")
    return OctopusA7Review(
        ceiling="A7",
        proposed_arms=proposal.selected_arms,
        missing_a6_proof=tuple(gate["a6_missing"]),
        missing_a7_proof=tuple(gate["a7_missing"]),
    )

# Evolution Intelligence is a capability within SMI metacognition.
# Intelligent Evolution is the rule governing its improvement cycles.
# This is a review contract, not autonomous execution or self-modification.
EVOLUTION_INTELLIGENCE_CAPABILITY = "Evolution Intelligence"
INTELLIGENT_EVOLUTION_LAW = "Intelligent Evolution"
EVOLUTION_QUALITY_GATES: tuple[str, ...] = (
    "stability", "clarity", "pace", "performance",
    "accuracy", "consistency", "reliability", "quality",
)


@dataclass(frozen=True)
class IntelligentEvolutionReview:
    """Advisory action/result/reflection/refinement review, never a Green receipt."""

    action: str
    result: str
    reflection: str
    refinement: str
    proposed_next_action: str
    evidence_assessment: MindAssessment
    decision: Literal["REFINE", "HOLD"]
    missing_quality_proof: tuple[str, ...] = EVOLUTION_QUALITY_GATES
    changed_method: bool = False
    repeat_authorized: bool = False
    deployment_authorized: bool = False
    self_modification_authorized: bool = False
    advisory_only: bool = True
    founder_final: bool = True


def review_intelligent_evolution(
    *,
    action: str,
    result: str,
    reflection: str,
    refinement: str,
    proposed_next_action: str,
    evidence: tuple[OAPEvidence, ...] = (),
) -> IntelligentEvolutionReview:
    """Review learning from a result without rewarding blind repetition.

    All evidence remains untrusted until separately authenticated by existing
    SMI/HRM/Guardian readback. Meaningful reflection and a changed proposed
    method are necessary for a REFINE recommendation, not sufficient for
    execution, deployment, claimed progress or Green Gate certification.
    """
    fields = (action, result, reflection, refinement, proposed_next_action)
    if any(not isinstance(value, str) or not value.strip() for value in fields):
        raise ValueError("Action, result, reflection, refinement and next action required")

    normalized = tuple(value.strip() for value in fields)
    current, observed, learned, improvement, next_action = normalized
    assessment = assess_oap_evidence(
        observed, evidence, required_kinds=("runtime", "test"),
    )
    changed = next_action.casefold() != current.casefold()
    # Even a changed action is held if its reflection/refinement is just a
    # verbatim restatement of the result or the proposed action.
    substantive = (
        learned.casefold() not in {observed.casefold(), current.casefold()}
        and improvement.casefold() not in {
            observed.casefold(), current.casefold(), learned.casefold(),
        }
    )
    decision: Literal["REFINE", "HOLD"] = (
        "REFINE" if changed and substantive
        and assessment.verdict != "HOLD" else "HOLD"
    )
    return IntelligentEvolutionReview(
        action=current,
        result=observed,
        reflection=learned,
        refinement=improvement,
        proposed_next_action=next_action,
        evidence_assessment=assessment,
        decision=decision,
        changed_method=changed,
    )


@dataclass(frozen=True)
class OctopusCycleAssessment:
    """Read-only coordination result for the existing SMI health-probe cycle."""

    status: str
    selected_arms: tuple[str, ...]
    missing_evidence: tuple[str, ...]
    action_required: str
    eight_arm_execution_verified: bool = False
    execution_granted: bool = False
    runtime_activation_proven: bool = False
    founder_final: bool = True


def assess_octopus_runtime_cycle(cycle: Mapping[str, object]) -> OctopusCycleAssessment:
    """Route actual SMI health evidence, never launch workers or infer A7.

    Designed for the *existing* organism health probe. This assessment does
    not create a job, access private data, self-approve or claim arm execution.
    """
    if not isinstance(cycle, Mapping):
        raise ValueError("SMI cycle evidence must be a mapping")
    invariants = cycle.get("production_invariants")
    if not isinstance(invariants, Mapping):
        invariants = {}
    locked = invariants.get("execution_locked") is True
    human = invariants.get("human_authority_final") is True
    total = cycle.get("gates_total")
    green = cycle.get("gates_green")
    valid_counts = (
        type(total) is int and type(green) is int
        and 0 < total and 0 <= green <= total
    )
    if not locked or not human:
        arms = ("OBSERVE", "TRACE", "RECOVER", "VERIFY")
        missing = tuple(
            name for name, proven in (
                ("execution_lock", locked),
                ("human_authority", human),
            ) if not proven
        )
        status = "HOLD"
        action = "RESTORE_GOVERNANCE_INVARIANTS"
    elif not valid_counts:
        arms = ("OBSERVE", "TRACE", "VERIFY")
        missing = ("valid_health_gate_denominator",)
        status = "UNKNOWN"
        action = "RETRIEVE_VERIFIED_HEALTH_GATES"
    elif green < total or cycle.get("health_status") != "healthy":
        arms = ("OBSERVE", "TRACE", "PLAN", "COORDINATE", "VERIFY")
        missing = ("health_gates_or_runtime_health",)
        status = "INVESTIGATE"
        action = "REVIEW_FAILED_HEALTH_GATES"
    else:
        arms = ("OBSERVE", "VERIFY")
        missing = ("independent_octopus_arm_execution_receipts",)
        status = "REVIEW"
        action = "VERIFY_ARM_EXECUTION_INDEPENDENTLY"
    review_octopus_arms(arms)
    return OctopusCycleAssessment(
        status=status,
        selected_arms=arms,
        missing_evidence=missing,
        action_required=action,
    )
