"""Bounded Founder Command Centre intent receipts, never execution authority.

Only actual authenticated Founder requests may call record_command_scope. A
successful receipt records a selected scope/approval intent, not a completed
tool action, external publication, deployment, or Green Gate.
"""
from __future__ import annotations

import hashlib
import re
from typing import Any
from uuid import UUID

from . import smi_receipt_backend

MISSION_IDS = frozenset({
    "command", "chat", "war", "studio", "distribution", "hrm",
    "library", "spot", "sika", "lab", "media",
})
DECISIONS = frozenset({"SELECT", "APPROVE_NEXT_SCOPE"})
DEPTHS = frozenset({3, 7, 21})
MODES = frozenset({"AUTO", "MANUAL"})


def _owner_digest(identity_id: object) -> str:
    try:
        owner = str(UUID(str(identity_id)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError("invalid_founder_identity") from exc
    return hashlib.sha256(("smi-command-scope-v1:" + owner).encode()).hexdigest()


_RECEIPT_ID = re.compile(r"^smi-[0-9a-f]{32}$")


def record_command_scope(payload: object, *, identity_id: object) -> dict[str, Any]:
    """Record a narrowly bounded command selection with durable readback.

    Fail closed on unavailable receipt storage: local SQLite fallback is
    unsuitable for claiming a durable Founder decision.
    """
    owner_digest = _owner_digest(identity_id)
    if not isinstance(payload, dict):
        raise TypeError("invalid_command_scope")
    mode = payload.get("mode")
    decision = payload.get("decision")
    depth = payload.get("depth")
    missions = payload.get("missions")
    if (
        type(mode) is not str or mode not in MODES
        or type(decision) is not str or decision not in DECISIONS
        or type(depth) is not int or depth not in DEPTHS
        or not isinstance(missions, list)
        or not 1 <= len(missions) <= len(MISSION_IDS)
        or any(type(item) is not str or item not in MISSION_IDS for item in missions)
        or len(missions) != len(set(missions))
    ):
        raise ValueError("invalid_command_scope")

    receipt = smi_receipt_backend.write_receipt(
        "agent_tool_connection_receipt",
        {
            "brain_part": "smi_command_centre",
            "gate": depth,
            "command": "founder_scope_decision",
            "signal": "🟣",
            "guardian": "scope_only",
            "green_gate": "not_execution_or_production_proof",
            "founder_final": "required_for_consequential_action",
            "safe_payload": {
                "owner_digest": owner_digest,
                "mode": mode,
                "depth": depth,
                "missions": sorted(missions),
                "decision": decision,
                "scope_only": True,
                "executed": False,
                "approval_grants_execution": False,
                "whole_smi_green": False,
            },
        },
        require_durable=True,
    )
    durable = (
        receipt.get("ok") is True
        and receipt.get("durable") is True
        and receipt.get("read_back_ok") is True
        and receipt.get("fallback_used") is False
    )
    return {
        "recorded": durable,
        "decision": decision,
        "missions": sorted(missions),
        "mode": mode,
        "depth": depth,
        "receipt_id": receipt.get("receipt_id") if durable else None,
        "state": "scope_recorded" if durable else "durable_receipt_unavailable",
        "executed": False,
        "whole_smi_green": False,
        "human_authority_final": True,
    }


def load_command_scope(*, identity_id: object, receipt_id: object) -> dict[str, Any]:
    """Reopen only the matching Founder's durably stored scope; never execute."""
    owner_digest = _owner_digest(identity_id)
    if not isinstance(receipt_id, str) or not _RECEIPT_ID.fullmatch(receipt_id):
        raise ValueError("invalid_scope_receipt")
    read = smi_receipt_backend.read_command_scope_receipt(receipt_id, owner_digest)
    if read is None:
        return {"found": False, "state": "not_found", "executed": False}
    if read.get("available") is False:
        return {"found": False, "state": "durable_receipt_unavailable", "executed": False}
    payload = read.get("payload")
    if (
        not isinstance(payload, dict)
        or payload.get("owner_digest") != owner_digest
        or payload.get("scope_only") is not True
        or payload.get("executed") is not False
        or payload.get("approval_grants_execution") is not False
    ):
        return {"found": False, "state": "not_found", "executed": False}
    missions = payload.get("missions")
    if (
        payload.get("mode") not in MODES
        or type(payload.get("depth")) is not int
        or payload["depth"] not in DEPTHS
        or payload.get("decision") not in DECISIONS
        or not isinstance(missions, list)
        or not missions
        or len(missions) != len(set(missions))
        or any(type(item) is not str or item not in MISSION_IDS for item in missions)
    ):
        return {"found": False, "state": "not_found", "executed": False}
    return {
        "found": True, "state": "saved_scope_loaded",
        "receipt_id": receipt_id,
        "mode": payload["mode"], "depth": payload["depth"],
        "missions": missions, "decision": payload["decision"],
        "executed": False, "whole_smi_green": False,
        "human_authority_final": True,
    }
