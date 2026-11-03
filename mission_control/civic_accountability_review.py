"""Read-only SMI civic accountability projection. No passports or action routes."""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from . import agents

BRANCHES = (
    "police", "cid", "fbi", "cia", "mi5", "mi6",
    "military", "undercover", "emergency",
)
FOUNDER_DECISIONS = (
    "unified_smi_mission_upgrade",
    "independent_accountability_review",
    "specialist_supervised_review",
)
ALLOWED_REVIEW_STATES = frozenset({
    "draft", "needs_evidence", "reviewed_with_dissent",
    "founder_scope_approved", "held", "rejected",
})


def civic_accountability_snapshot() -> dict[str, Any]:
    """Expose review-only metadata; never mutate or copy passport permissions."""
    ids = tuple(str(agent["agent_id"]) for agent in agents.AGENT_REGISTRY)
    if len(ids) != len(set(ids)) or len(ids) != agents.LOCKED_AGENT_COUNT:
        raise ValueError("Canonical registry integrity failure")
    return {
        "mode": "read_only_review",
        "activation": "disabled",
        "founder_scope_approved": True,
        "founder_activation_approved": False,
        "green_gate": "HOLD",
        "canonical_agent_count": len(ids),
        "canonical_agent_ids": ids,
        "decisions": FOUNDER_DECISIONS,
        "specialist_review_branches": tuple(
            {"branch": name, "status": "supervised_candidate",
             "agent_id": None, "permissions": ()}
            for name in BRANCHES
        ),
        "requires": ("authenticated_founder", "guardian", "hrm_receipt",
                     "green_gate_proof", "separate_founder_activation"),
    }


def validate_review_entry(entry: Mapping[str, Any]) -> dict[str, Any]:
    """Fail closed for invalid/unsubstantiated reviews; no authority escalation."""
    required = ("case_id", "purpose", "source_links", "dissent", "status")
    if any(key not in entry for key in required):
        raise ValueError("Missing mandatory review fields")
    if not isinstance(entry["case_id"], str) or not entry["case_id"].strip():
        raise ValueError("Invalid case identifier")
    if not isinstance(entry["purpose"], str) or not entry["purpose"].strip():
        raise ValueError("Invalid purpose")
    links = entry["source_links"]
    if not isinstance(links, (tuple, list)) or not links or not all(
        isinstance(link, str) and link.startswith("https://") for link in links
    ):
        raise ValueError("Evidence must have HTTPS source links")
    if not isinstance(entry["dissent"], str):
        raise TypeError("Dissent must remain recorded, even if none is submitted")
    if entry["status"] not in ALLOWED_REVIEW_STATES:
        raise ValueError("Unapproved review status or activation attempt")
    if "agent_id" in entry or "permissions" in entry:
        raise ValueError("Review cannot grant agent identity or permissions")
    return {
        "case_id": entry["case_id"],
        "purpose": entry["purpose"],
        "source_links": tuple(links),
        "dissent": entry["dissent"],
        "status": entry["status"],
        "activation": "disabled",
        "green_gate": "HOLD",
    }
