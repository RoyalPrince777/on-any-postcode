"""Private Founder chat directives for the existing SMI/War Room protocol.

Deterministic, side-effect free and deliberately not an approval/execution path.
The conversation history is supplied by the already authenticated chat runtime;
no raw history, personal details or secrets enter this result.
"""
from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any

from . import intelligence_lenses, smi_brain_protocol, smi_deep_dive_protocol

_CONTINUE = frozenset({"🟣", "continue", "continue 🟣", "🟣 continue", "next", "🟣 smi", "smi auto"})
_APPROVE = frozenset({"🟢", "approved", "approve", "🟢 approved"})
_NO_MISSION = frozenset(_CONTINUE | _APPROVE | {"stop", "pause", "resume", "🟣 smi 21", "smi 21"})
_WAR_ROOM = re.compile(r"\bwar[\s-]*room\b", re.IGNORECASE)
_DEPTH_21 = re.compile(r"(?:\bsmi\s*(?:auto\s*)?21\b|\bdeep\s*dive\b|\b21\s*protocol\b)", re.IGNORECASE)


def _has_context(history: Sequence[Mapping[str, object]] | None) -> bool:
    """Only supplied, conversation-owned turns can establish a current mission."""
    for item in history or ():
        if item.get("role") not in {"user", "assistant"}:
            continue
        content = str(item.get("content") or "").strip()
        if content and (content.casefold() not in _NO_MISSION) and (
            item.get("role") == "user" or len(content) >= 40
        ):
            return True
    return False


def resolve_turn(
    message: object,
    history: Sequence[Mapping[str, object]] | None,
    *,
    requested_mode: object = "auto",
) -> dict[str, Any]:
    """Map a short Founder command to review guidance, never execution authority.

    The model receives flags/instructions, not an invented project or raw history.
    Explicit Manual depth remains Manual even when a previous turn used War Room.
    """
    text = str(message or "").strip()
    lowered = re.sub(r"\s+", " ", text.casefold())
    has_context = _has_context(history)
    requested = str(requested_mode or "auto").strip().casefold()
    explicit_war = bool(_WAR_ROOM.search(text))
    explicit_21 = bool(_DEPTH_21.search(text))
    recent_war = any(
        _WAR_ROOM.search(str(item.get("content") or ""))
        for item in (history or ())[-12:]
        if item.get("role") in {"user", "assistant"}
    )

    if lowered in _APPROVE:
        intent = "FOUNDER_DESIGN_APPROVAL"
    elif lowered in _CONTINUE or (text.startswith("🟣") and len(text) <= 32):
        intent = "CONTINUE_CURRENT_MISSION"
    elif "jog memory" in lowered or "fetch memory" in lowered:
        intent = "RECALL_GOVERNED_CONTEXT"
    elif lowered in {"stop", "⏹", "⏹️", "stop 🛑"}:
        intent = "REQUEST_STOP"
    elif explicit_war:
        intent = "WAR_ROOM_REVIEW"
    else:
        intent = "NORMAL_REQUEST"

    wants_war = bool(
        explicit_war
        or (intent == "CONTINUE_CURRENT_MISSION" and recent_war and has_context)
    )
    preferred_depth = 21 if explicit_21 or wants_war else None
    if requested != "auto":
        preferred_depth = None  # The human's explicit selector takes precedence.

    return {
        "intent": intent,
        "history_has_mission_context": has_context,
        "war_room_requested": wants_war,
        "preferred_depth": preferred_depth,
        "response_contract": "MISSION / MODE / ALIGNMENT / PROTOCOL / DONE / LOCKED / NEXT",
        "review_may_continue": has_context and intent == "CONTINUE_CURRENT_MISSION",
        "design_approval_is_execution_authority": False,
        "review_votes_grant_authority": False,
        "production_status_requires_runtime_evidence": True,
        "execution_granted": False,
        "human_authority_final": True,
    }


def instruction() -> str:
    """Short shared protocol for local, bridge, and compatibility generation."""
    return (
        "FOUNDER WORKFLOW: Continue the existing mission on a purple/continue "
        "directive only when the supplied authenticated conversation or governed "
        "memory establishes it. Do not start an unrelated new simulation or invent "
        "missing context. SMI AUTO chooses 3/7/21 review depth; Manual stays manual; "
        "War Room uses 21-depth and can invoke 7X accumulated challenge. "
        "Preserve seven councils, seven canonical judge seats, 26 lenses, "
        "Guardian/Aegis, dissent, seven-star evidence, End Review, HRM/JOOG "
        "and Founder Final. Treat judges as rule lenses unless independent agents "
        "actually ran. Green approves only the explicitly identified decision/gate; "
        "a chat emoji is NEVER a signed exact-action receipt, tool execution, "
        "merge, deployment or production certification. For major work retain "
        "25/50/75/100 quarters separately from 3/7/21 depth. Never advance a "
        "quarter without evidence. Summarise in concise MISSION / MODE / "
        "ALIGNMENT / PROTOCOL / DONE / LOCKED / NEXT; retain the full review "
        "in an actual receipt only if the runtime persisted it. STOP must use a "
        "verified cancellation path; a text-only response cannot claim halt."
    )


def status() -> dict[str, object]:
    """Inspect canonical sources without duplicating the War Room registry."""
    return {
        "component": "SMI Founder War Room Chat Workflow",
        "mode": "private_advisory_only",
        "council_count": 7,
        "judge_names": tuple(
            judge["name"] for judge in smi_brain_protocol.WAR_ROOM_JUDGES
        ),
        "lens_ids": intelligence_lenses.FULL_LENS_IDS,
        "seven_x": tuple(
            item["name"] for item in smi_deep_dive_protocol.SEVEN_X_PASSES
        ),
        "seven_star": smi_deep_dive_protocol.SEVEN_STAR_GATE,
        "authority_granted": False,
        "human_authority_final": True,
    }
