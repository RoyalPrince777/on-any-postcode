"""Founder-only, read-only Hybrid Agents HQ rooms and canonical home placement.

Every registered agent keeps one canonical family, intelligence world and home
system. Matrix film-home references are advisory provenance, never new agents.
Collaboration never transfers an agent's identity or grants execution.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from . import agents


def _family_index() -> dict[str, Mapping[str, Any]]:
    families: dict[str, Mapping[str, Any]] = {}
    for family in agents.INTELLIGENCE_FAMILIES:
        family_id = str(family.get("id") or "")
        if not family_id or family_id in families:
            raise ValueError("Invalid or duplicate canonical family")
        if not all(str(family.get(key) or "").strip() for key in ("name", "world_id", "home_system")):
            raise ValueError("Canonical family missing home alignment")
        families[family_id] = family
    return families


def _home_profile(
    agent: Mapping[str, Any], families: Mapping[str, Mapping[str, Any]]
) -> dict[str, Any]:
    family_id = str(agent.get("family_id") or "")
    if family_id not in families:
        raise ValueError("Agent has no registered canonical family")
    family = families[family_id]
    film_home = None
    # Newer canonical agent registries include distinct Matrix film-home groups.
    # Reuse the canonical resolver when present; never duplicate its group roster.
    resolver = getattr(agents, "matrix_home_for", None)
    if family_id == "matrix" and callable(resolver):
        film_home = resolver(str(agent.get("name") or ""))
        if film_home is not None and film_home.get("family_id") != "matrix":
            raise ValueError("Matrix home reference has mismatched family")
    return {
        "family_id": family_id,
        "family_name": str(family["name"]),
        "world_id": str(family["world_id"]),
        "home_system": str(family["home_system"]),
        "home_group": film_home,
    }


def room_directory() -> dict[str, Any]:
    """Project all agents, individual rooms and their original family homes."""
    registry = agents.AGENT_REGISTRY
    ids = [str(agent["agent_id"]) for agent in registry]
    if any(not agent_id for agent_id in ids) or len(ids) != len(set(ids)):
        raise ValueError("Invalid or duplicate canonical agent passport")
    families = _family_index()
    profiles = {agent_id: _home_profile(agent, families)
                for agent_id, agent in zip(ids, registry)}
    rooms: list[dict[str, Any]] = [
        {
            "id": "all_agents",
            "kind": "all_agents",
            "name": "All Agents",
            "agent_ids": tuple(ids),
            "home_system": None,
            "world_id": None,
        }
    ]
    rooms.extend(
        {
            "id": f"agent:{agent_id}",
            "kind": "individual",
            "name": str(agent["name"]),
            "agent_ids": (agent_id,),
            **profiles[agent_id],
        }
        for agent_id, agent in zip(ids, registry)
    )
    for family_id, family in families.items():
        members = tuple(
            agent_id for agent_id in ids if profiles[agent_id]["family_id"] == family_id
        )
        rooms.append(
            {
                "id": f"family:{family_id}",
                "kind": "family",
                "name": str(family["name"]),
                "agent_ids": members,
                "family_id": family_id,
                "family_name": str(family["name"]),
                "world_id": str(family["world_id"]),
                "home_system": str(family["home_system"]),
            }
        )
    return {
        "scope": "founder_only",
        "mode": "read_only_room_directory",
        "source": "canonical_agent_registry",
        "home_assignment_source": "canonical_family_alignment",
        "human_authority": "Founder Final",
        "agent_count": len(ids),
        "rooms": tuple(rooms),
        "messages": (),
        "message_history_available": False,
        "autonomous_agent_chat": False,
        "cross_family_collaboration_active": False,
        "permissions_changed": False,
        "can_execute": False,
    }


def room_context(room_id: str) -> dict[str, Any]:
    """Return registered members and their original homes, never a second roster."""
    if not isinstance(room_id, str) or not room_id.strip():
        raise ValueError("Room ID required")
    directory = room_directory()
    room = next((item for item in directory["rooms"] if item["id"] == room_id), None)
    if room is None:
        raise ValueError("Unknown canonical room")
    families = _family_index()
    by_id: dict[str, Mapping[str, Any]] = {
        str(agent["agent_id"]): agent for agent in agents.AGENT_REGISTRY
    }
    return {
        "room": room,
        "members": tuple(
            {
                "agent_id": agent_id,
                "name": str(by_id[agent_id]["name"]),
                **_home_profile(by_id[agent_id], families),
            }
            for agent_id in room["agent_ids"]
        ),
        "mode": "read_only_context",
        "actual_messages": (),
        "agent_responses_generated": False,
        "founder_final": True,
        "can_execute": False,
    }
