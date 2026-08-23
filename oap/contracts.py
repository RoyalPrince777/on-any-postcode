"""Shared immutable contracts for the OAP Digital Organism runtime."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any


def utc_now() -> datetime:
    """Return an aware UTC timestamp."""

    return datetime.now(timezone.utc)


class OutputState(StrEnum):
    """The only outputs the SMI Brain may produce independently."""

    RECOMMENDATION_READY = "RECOMMENDATION_READY"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    BLOCK_REQUEST = "BLOCK_REQUEST"
    SYSTEM_LOG_ONLY = "SYSTEM_LOG_ONLY"


class SignalLevel(StrEnum):
    """Human-first operational safety levels."""

    GREEN = "GREEN"
    YELLOW = "YELLOW"
    ORANGE = "ORANGE"
    RED = "RED"
    WHITE = "WHITE"


class ApprovalDecision(StrEnum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


@dataclass(frozen=True, slots=True)
class BrainRequest:
    """A signal delivered to SMI through NEXUS."""

    request_id: str
    identity_id: str
    content: str
    task_type: str = "GENERAL"
    metadata: dict[str, Any] = field(default_factory=dict)
    high_impact: bool = False
    created_at: datetime = field(default_factory=utc_now)


@dataclass(frozen=True, slots=True)
class IdentityRecord:
    """Verified identity data supplied by the canonical Identity system."""

    identity_id: str
    identity_type: str
    authority_level: int
    status: str = "ACTIVE"
    permissions: frozenset[str] = field(default_factory=frozenset)
    roles: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class PermissionDecision:
    allowed: bool
    identity_id: str
    authority_level: int | None
    reason: str
    required_permission: str
    status: str


@dataclass(frozen=True, slots=True)
class NexusEnvelope:
    """A transported signal; NEXUS carries it but never decides it."""

    request: BrainRequest
    route: tuple[str, ...]
    received_at: datetime


@dataclass(frozen=True, slots=True)
class FocusedSignal:
    """Thalamus-filtered input safe for internal analysis."""

    request_id: str
    identity_id: str
    task_type: str
    content: str
    metadata: dict[str, Any]
    high_impact: bool
    tags: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class MemoryItem:
    memory_id: str
    task_type: str
    summary: str
    output_state: str
    created_at: datetime


@dataclass(frozen=True, slots=True)
class ContextSnapshot:
    memories: tuple[MemoryItem, ...]
    world_state: dict[str, Any]
    retrieved_at: datetime


@dataclass(frozen=True, slots=True)
class OrganFinding:
    organ_id: str
    summary: str
    confidence: float
    tags: tuple[str, ...] = ()
    signal_level: SignalLevel = SignalLevel.GREEN


@dataclass(frozen=True, slots=True)
class IntegratedAnalysis:
    summary: str
    findings: tuple[OrganFinding, ...]
    signal_level: SignalLevel
    confidence: float


@dataclass(frozen=True, slots=True)
class SafetyFinding:
    system: str
    code: str
    message: str
    signal_level: SignalLevel
    blocks: bool = False


@dataclass(frozen=True, slots=True)
class SafetyDecision:
    passed: bool
    signal_level: SignalLevel
    findings: tuple[SafetyFinding, ...]
    human_review_required: bool


@dataclass(frozen=True, slots=True)
class AdvisorSelection:
    agent_ids: tuple[str, ...]
    reason: str


@dataclass(frozen=True, slots=True)
class ProviderResult:
    provider_id: str
    available: bool
    text: str
    error_code: str | None = None


@dataclass(frozen=True, slots=True)
class WarRoomReport:
    triggered: bool
    scenarios: tuple[str, ...]
    recommendation: str
    review_id: str = ""
    review_level: str = "ROUTINE"
    risk_score: int = 0
    confidence_score: int = 0
    findings: tuple[str, ...] = ()
    requires_human_approval: bool = True
    decision_authority: bool = False


@dataclass(frozen=True, slots=True)
class Recommendation:
    """SMI output. It is never an independent execute decision."""

    request_id: str
    output_state: OutputState
    summary: str
    rationale: tuple[str, ...]
    signal_level: SignalLevel
    advisor_ids: tuple[str, ...]
    provider_ids: tuple[str, ...]
    processing_states: tuple[str, ...]
    human_review_required: bool
    war_room: WarRoomReport
    created_at: datetime = field(default_factory=utc_now)

    @property
    def can_execute(self) -> bool:
        """SMI recommendations can never execute directly."""

        return False


@dataclass(frozen=True, slots=True)
class ApprovalReceipt:
    receipt_id: str
    request_id: str
    identity_id: str
    authority_level: int
    decision: ApprovalDecision
    issued_at: datetime
    expires_at: datetime
    nonce: str
    action_digest: str
    signature: str


@dataclass(frozen=True, slots=True)
class ActionPlan:
    request_id: str
    action_type: str
    payload: dict[str, Any]
    requires_human_approval: bool = True


@dataclass(frozen=True, slots=True)
class BuilderContext:
    """Verified context passed by Living Kernel to one Builder handler."""

    request_id: str
    receipt_id: str
    identity_id: str
    authority_level: int
    action_digest: str


def action_plan_digest(plan: ActionPlan) -> str:
    """Return a stable digest that binds Human approval to one exact plan."""

    canonical = json.dumps(
        {
            "request_id": plan.request_id,
            "action_type": plan.action_type,
            "payload": plan.payload,
            "requires_human_approval": plan.requires_human_approval,
        },
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class KernelResult:
    request_id: str
    state: str
    executed: bool
    reason: str
    processing_states: tuple[str, ...] = ()
    audit_event_id: str | None = None


@dataclass(frozen=True, slots=True)
class EvolutionProposal:
    proposal_id: str
    title: str
    description: str
    evidence: tuple[str, ...]
    requires_human_approval: bool = True
