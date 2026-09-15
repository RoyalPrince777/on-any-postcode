"""Canonical governed OAP system protocol.

Policy only: names and protocol selection never grant permissions, expose private
data, deploy, move money, or prove an external action succeeded.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from enum import Enum

from mission_control.hrm_agent_lifecycle import ReviewDepth, required_depth


class ProtocolLayer(str, Enum):
    OAP_OS = "OAP_OS"
    SMI = "SMI"
    OMNI = "OMNI"
    HYBRID = "HYBRID"
    CIVILISATION = "CIVILISATION"
    GUARDIAN = "GUARDIAN"
    HRM = "HRM"
    SIGNAL = "SIGNAL"


class ExecutionPath(str, Enum):
    DETERMINISTIC = "DETERMINISTIC"
    LOCAL_AI = "LOCAL_AI"
    CONNECTED_SERVICE = "CONNECTED_SERVICE"
    HUMAN_AUTHORITY = "HUMAN_AUTHORITY"


class HRMPlane(str, Enum):
    MIND = "MIND"
    BODY = "BODY"
    SOUL = "SOUL"


HRM_PLANES = (HRMPlane.MIND, HRMPlane.BODY, HRMPlane.SOUL)
HRM_PLANE_PURPOSE = {
    HRMPlane.MIND: "reasoning, evidence, understanding, architecture and judgement",
    HRMPlane.BODY: "execution readiness, infrastructure, capability, performance and real-world outcome",
    HRMPlane.SOUL: "purpose, human benefit, values, culture, consent and constitutional alignment",
}


@dataclass(frozen=True)
class ProtocolDecision:
    signal: str
    layers: tuple[ProtocolLayer, ...]
    execution_paths: tuple[ExecutionPath, ...]
    review_depth: ReviewDepth
    hrm_planes: tuple[HRMPlane, ...]
    human_authority_required: bool
    fail_closed: bool
    reason: str


CANONICAL_FLOW = (
    ProtocolLayer.SIGNAL,
    ProtocolLayer.OMNI,
    ProtocolLayer.SMI,
    ProtocolLayer.HYBRID,
    ProtocolLayer.CIVILISATION,
    ProtocolLayer.GUARDIAN,
    ProtocolLayer.HRM,
)
LAYER_PURPOSE = {
    ProtocolLayer.OAP_OS: "holds the governed OAP operating environment together",
    ProtocolLayer.SMI: "reasons, challenges and forms bounded judgement",
    ProtocolLayer.OMNI: "builds whole-system awareness without granting access",
    ProtocolLayer.HYBRID: "selects the minimum safe mix of execution paths",
    ProtocolLayer.CIVILISATION: "coordinates systems, intelligence families, formations and agents",
    ProtocolLayer.GUARDIAN: "enforces security, privacy, consent and permission boundaries",
    ProtocolLayer.HRM: "records Mind Body Soul evidence, decisions, receipts, outcomes and learning",
    ProtocolLayer.SIGNAL: "carries governed events and intelligence between layers",
}


def choose_protocol(
    signal: str,
    *,
    risk: str = "low",
    authority_change: bool = False,
    external_action: bool = False,
    private_data: bool = False,
    requested_paths: Iterable[ExecutionPath] = (),
) -> ProtocolDecision:
    clean_signal = str(signal).strip()
    paths = tuple(dict.fromkeys(requested_paths))
    human_required = authority_change or risk.lower() in {"high", "critical", "severe"}
    if external_action and not paths:
        paths = (ExecutionPath.HUMAN_AUTHORITY,)
        human_required = True
    if human_required and ExecutionPath.HUMAN_AUTHORITY not in paths:
        paths = paths + (ExecutionPath.HUMAN_AUTHORITY,)
    depth = required_depth(risk=risk, authority_change=authority_change or human_required)
    fail_closed = not clean_signal or (private_data and not paths)
    if not clean_signal:
        reason = "missing_signal"
    elif private_data and not paths:
        reason = "private_data_path_not_proven"
    elif human_required:
        reason = "human_authority_gate_required"
    else:
        reason = "minimum_safe_protocol_selected"
    return ProtocolDecision(
        clean_signal,
        CANONICAL_FLOW,
        paths,
        depth,
        HRM_PLANES,
        human_required,
        fail_closed,
        reason,
    )


def mind_body_soul_review(
    *, mind_evidence: bool, body_evidence: bool, soul_evidence: bool
) -> dict[str, object]:
    """Three-plane HRM gate. Missing evidence is visible and never silently green."""
    status = {
        HRMPlane.MIND: bool(mind_evidence),
        HRMPlane.BODY: bool(body_evidence),
        HRMPlane.SOUL: bool(soul_evidence),
    }
    missing = tuple(plane.value for plane, proven in status.items() if not proven)
    return {
        "planes": {plane.value: proven for plane, proven in status.items()},
        "all_proven": not missing,
        "missing": missing,
        "status": "PROVEN" if not missing else "REVIEW",
    }


def agent_handoff(
    requesting_agent: str,
    helping_agent: str,
    assignment: str,
    *,
    permitted_evidence: Iterable[str] = (),
) -> dict[str, object]:
    requester = str(requesting_agent).strip()
    helper = str(helping_agent).strip()
    work = str(assignment).strip()
    valid = bool(requester and helper and work)
    return {
        "type": "agent_to_agent_signal",
        "requesting_agent": requester,
        "helping_agent": helper,
        "assignment": work,
        "permitted_evidence": tuple(str(item) for item in permitted_evidence),
        "authority_transferred": False,
        "hrm_receipt_required": True,
        "mind_body_soul_required": True,
        "status": "READY" if valid else "LOCKED",
    }
