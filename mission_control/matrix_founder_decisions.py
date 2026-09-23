"""Founder-only bounded HOLD/BLOCK record for Matrix War Room review.

This is a genuine authenticated Founder decision *to withhold approval*, never a
verified specialist vote, an approved Matrix review, or execution authority.
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from . import authority, matrix_war_room, smi_receipt_backend


def record_hold(
    *, identity_id: str, signal: Mapping[str, Any], decision: str, reason: str
) -> dict[str, Any]:
    """Require canonical Human Authority and a valid consequential review envelope."""
    actor = str(identity_id or "").strip()
    if not actor or not authority.identity_is_authority(actor):
        raise PermissionError("human_authority_required")
    if decision not in {"HOLD", "BLOCK"}:
        raise ValueError("Only HOLD or BLOCK can be recorded through this path")
    reason = str(reason or "").strip()
    if not reason or len(reason) > 2000:
        raise ValueError("A bounded decision reason is required")
    pack = matrix_war_room.review_pack(signal)
    signal_id = str(pack["signal_id"]).strip()
    if not signal_id:
        raise ValueError("Signal ID required")
    receipt = smi_receipt_backend.write_receipt(
        "war_room_live_proof_receipt",
        {
            "brain_part": "matrix",
            "gate": 6,
            "command": "matrix_founder_hold",
            "signal": "🟠",
            "guardian": "required_separate_gate",
            "green_gate": "required_separate_gate",
            "founder_final": "not_approved",
            "safe_payload": {
                "signal_id": signal_id,
                "founder_identity_id": actor,
                "decision": decision,
                "reason": reason,
                "review_mode": "founder_hold_unverified_evidence",
                "evidence_verified": False,
                "actual_agent_votes": (),
                "founder_approved": False,
                "execution_granted": False,
            },
        },
        require_durable=True,
    )
    recorded = bool(
        receipt.get("ok") is True
        and receipt.get("read_back_ok") is True
        and receipt.get("durable") is True
        and receipt.get("fallback_used") is False
        and receipt.get("receipt_kind") == "war_room_live_proof_receipt"
    )
    return {
        "state": "founder_hold_recorded" if recorded else "founder_hold_unproven",
        "signal_id": signal_id,
        "decision": decision if recorded else None,
        "receipt": receipt,
        "actual_agent_votes": (),
        "evidence_verified": False,
        "founder_approved": False,
        "matrix_update_allowed": False,
        "execution_granted": False,
        "full_green": False,
    }
