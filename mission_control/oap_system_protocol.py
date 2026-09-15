"""Canonical governed OAP system protocol.

This module closes the naming/coordination gap between OAP OS, SMI, OMNI,
HYBRID, Civilisation Intelligence, Guardian, HRM and Signals. It is deliberately
policy-only: it does not grant permissions, expose private data, deploy, move
money, or claim an external action succeeded.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable

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


@dataclass(frozen=True)
class ProtocolDecision:
    signal: str
    layers: tuple[ProtocolLayer, ...]
    execution_paths: tuple[ExecutionPath, ...]
    review_depth: ReviewDepth
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
    ProtocolLayer.HRM: "records evidence, decisions, receipts, outcomes and learning",
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
    """Return a bounded protocol decision; never executes the requested action."""
    clean_signal = str(signal).strip()
    paths = tuple(dict.fromkeys(requested_paths))
    human_required = authority_change or risk.lower() in {"high", "critical", "severe"}

    if external_action and not paths:
        paths = (ExecutionPath.HUMAN_AUTHORITY,)
        human_required = True

    if human_required and ExecutionPath.HUMAN_AUTHORITY not in paths:
        paths = paths + (ExecutionPath.HUMAN_AUTHORITY,)

    depth = required_depth(risk=risk, authority_change=authority_change or human_required)
    fail_closed = not clean_signal or (external_action and not paths) or private_data and not paths

    if not clean_signal:
        reason = "missing_signal"
    elif private_data and not paths:
        reason = "private_data_path_not_proven"
    elif human_required:
        reason = "human_authority_gate_required"
    else:
        reason = "minimum_safe_protocol_selected"

    return ProtocolDecision(
        signal=clean_signal,
        layers=CANONICAL_FLOW,
        execution_paths=paths,
        review_depth=depth,
        human_authority_required=human_required,
        fail_closed=fail_closed,
        reason=reason,
    )


def agent_handoff(
    requesting_agent: str,
    helping_agent: str,
    assignment: str,
    *,
    permitted_evidence: Iterable[str] = (),
) -> dict[str, object]:
    """Create an auditable agent-to-agent Signal without transferring authority."""
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
        "status": "READY" if valid else "LOCKED",
    }
