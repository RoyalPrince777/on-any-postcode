"""Founder-only, read-only Hybrid Agents HQ room directory.

Rooms are projections of the canonical registry, not chat sessions or agents.
No messages are fabricated, stored, sent, or executed by this module.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from . import agents


def room_directory() -> dict[str, Any]:
    """Project All Agents, individual rooms and canonical family rooms."""
    registry = agents.AGENT_REGISTRY
    ids = [str(agent["agent_id"]) for agent in registry]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate canonical agent passport")
    families = {str(family["id"]): family for family in agents.INTELLIGENCE_FAMILIES}
    rooms: list[dict[str, Any]] = [
        {
            "id": "all_agents",
            "kind": "all_agents",
            "name": "All Agents",
            "agent_ids": tuple(ids),
        }
    ]
    rooms.extend(
        {
            "id": f"agent:{agent['agent_id']}",
            "kind": "individual",
            "name": str(agent["name"]),
            "agent_ids": (str(agent["agent_id"]),),
        }
        for agent in registry
    )
    for family_id, family in families.items():
        members = tuple(
            str(agent["agent_id"])
            for agent in registry
            if agent.get("family_id") == family_id
        )
        rooms.append(
            {
                "id": f"family:{family_id}",
                "kind": "family",
                "name": str(family["name"]),
                "agent_ids": members,
            }
        )
    return {
        "scope": "founder_only",
        "mode": "read_only_room_directory",
        "source": "canonical_agent_registry",
        "human_authority": "Founder Final",
        "agent_count": len(ids),
        "rooms": tuple(rooms),
        "messages": (),
        "message_history_available": False,
        "autonomous_agent_chat": False,
        "permissions_changed": False,
        "can_execute": False,
    }


def room_context(room_id: str) -> dict[str, Any]:
    """Return only registered room membership; reject guessed identities."""
    if not isinstance(room_id, str) or not room_id.strip():
        raise ValueError("Room ID required")
    directory = room_directory()
    room = next(
        (item for item in directory["rooms"] if item["id"] == room_id),
        None,
    )
    if room is None:
        raise ValueError("Unknown canonical room")
    by_id: dict[str, Mapping[str, Any]] = {
        str(agent["agent_id"]): agent for agent in agents.AGENT_REGISTRY
    }
    return {
        "room": room,
        "members": tuple(
            {"agent_id": agent_id, "name": str(by_id[agent_id]["name"])}
            for agent_id in room["agent_ids"]
        ),
        "mode": "read_only_context",
        "actual_messages": (),
        "agent_responses_generated": False,
        "founder_final": True,
        "can_execute": False,
    }
