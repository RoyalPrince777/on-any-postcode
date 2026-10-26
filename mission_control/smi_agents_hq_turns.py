"""Founder-inclusive SMI Agents HQ turn contract.

This is a bounded conversation *admission* layer, not a simulated council,
inference engine, agent worker, or authorisation to execute tools.
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from mission_control import agents

MAX_MESSAGE_CHARS = 2000


def admit_council_turn(
    *,
    speaker: str,
    message: str,
    founder_authenticated: bool = False,
) -> dict[str, Any]:
    """Admit Founder input or a uniquely registered ACTIVE agent's text.

    Agent-origin text is unverified until the runtime separately authenticates
    its sender. No stored conversation, impersonation, votes or tool execution.
    """
    if not isinstance(speaker, str) or not isinstance(message, str):
        raise ValueError("speaker_and_message_must_be_text")
    name = speaker.strip()
    body = message.strip()
    if not name or not body or len(body) > MAX_MESSAGE_CHARS:
        raise ValueError("invalid_council_turn")
    if name.casefold() == "founder":
        if not founder_authenticated:
            raise PermissionError("founder_authentication_required")
        identity = {"type": "human", "name": "Founder", "authority": "founder_final"}
    else:
        if founder_authenticated:
            raise PermissionError("founder_cannot_impersonate_agent")
        matches = [agent for agent in agents.AGENT_REGISTRY
                   if str(agent.get("name", "")).casefold() == name.casefold()]
        if len(matches) != 1 or not matches[0].get("agent_id"):
            raise PermissionError("unique_agent_passport_required")
        agent = matches[0]
        if agent.get("registry_status") != "ACTIVE":
            raise PermissionError("active_agent_passport_required")
        identity = {"type": "agent_candidate_message", "name": agent["name"],
                    "agent_id": agent["agent_id"],
                    "authority": "none_sender_authentication_pending"}
    return {
        "speaker": identity, "message": body,
        "admission_only": True, "runtime_sender_verified": False,
        "live_agent_dialogue_proven": False, "execution_authorised": False,
        "vote_recorded": False, "career_star_awarded": False,
        "founder_final": True,
    }
