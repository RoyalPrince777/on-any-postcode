"""Read-only Matrix Signal -> War Room evidence handoff.

A Signal is a review request, not a verified agent vote, HRM write, or approval.
The adapter accepts only the canonical registered-only, non-executing envelope
and keeps unverified evidence explicitly unverified.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from . import matrix_signal_bus


def review_pack(signal: Mapping[str, Any]) -> dict[str, Any]:
    """Prepare a fail-closed review-only pack for the existing War Room."""

    if not isinstance(signal, Mapping):
        raise ValueError("Matrix Signal mapping required")
    sender = signal.get("sender")
    if sender not in matrix_signal_bus.registered_matrix_names():
        raise ValueError("Registered Matrix sender required")
    if (
        signal.get("state") != "routed_for_review"
        or signal.get("sender_channel") != matrix_signal_bus.MATRIX_ROLE_CHANNELS[sender]
        or signal.get("trinity_coordination_required") is not True
        or signal.get("smi_interpretation_required") is not True
        or signal.get("hrm_receipt_required") is not True
        or signal.get("guardian_required") is not True
        or signal.get("green_gate_required") is not True
        or signal.get("human_authority_final") is not True
        or signal.get("execution_granted") is not False
        or signal.get("external_action_taken") is not False
        or signal.get("self_approval_allowed") is not False
        or signal.get("permission_change_allowed") is not False
        or signal.get("agent_creation_allowed") is not False
    ):
        raise ValueError("Matrix Signal governance envelope invalid")
    if signal.get("war_room_required") is not True or signal.get("human_authority_required") is not True:
        raise ValueError("Consequential Matrix review required")
    topic = signal.get("topic")
    if not isinstance(topic, str) or not topic.strip():
        raise ValueError("Matrix review topic required")
    raw_evidence = signal.get("evidence")
    if not isinstance(raw_evidence, (tuple, list)) or not all(
        isinstance(item, str) and item.strip() for item in raw_evidence
    ):
        raise ValueError("Matrix evidence list invalid")
    topology = matrix_signal_bus.topology()
    candidates = tuple(
        {"name": item["name"], "status": "passport_review", "can_emit_signal": False}
        for item in topology["participants"]
        if item["status"] == "passport_review"
    )
    return {
        "name": "Matrix -> War Room review pack",
        "mode": "read_only_unverified_signal_handoff",
        "signal_id": str(signal.get("signal_id") or ""),
        "sender": sender,
        "topic": topic.strip(),
        "evidence_claims": tuple(raw_evidence),
        "evidence_verified": False,
        "actual_agent_votes": (),
        "simulated_specialist_views": (),
        "registered_core_count": topology["registered_count"],
        "extended_review_count": topology["extended_review_count"],
        "candidate_review_roster": candidates,
        "review_required": True,
        "trinity_coordination_required": True,
        "smi_interpretation_required": True,
        "hrm_receipt_required": True,
        "hrm_receipt_recorded": False,
        "guardian_required": True,
        "green_gate_required": True,
        "human_authority_final": True,
        "founder_approved": False,
        "execution_granted": False,
        "external_action_taken": False,
        "full_green": False,
        "next_gate": "Verify source evidence and actual review; obtain Guardian, Green Gate, HRM receipt and Founder Final.",
    }
