"""Pure, read-only individual agent achievement calculations.

This module does not award stars, persist decisions, or change agent authority.
It only summarizes externally reviewed award records against the canonical registry.
"""
from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from . import agents

STAR_VALUES = {"minor": 1, "major": 3, "protocol": 5}
REQUIRED_JUDGES = ("shere_khan", "fox", "bagheera", "gorilla")


def career_rankings(awards: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Aggregate approved unique achievements; reject invalid evidence.

    A single movement ID can be credited to distinct contributors, but not
    twice to the same agent. All four independent review decisions are required.
    """
    registry = {str(a["agent_id"]): a for a in agents.AGENT_REGISTRY}
    totals = {key: 0 for key in registry}
    seen: set[tuple[str, str]] = set()
    for award in awards:
        agent_id = str(award.get("agent_id", ""))
        movement_id = str(award.get("movement_id", "")).strip()
        evidence = str(award.get("evidence", "")).strip()
        kind = str(award.get("kind", ""))
        if agent_id not in registry or not movement_id or not evidence or kind not in STAR_VALUES:
            raise ValueError("Invalid agent, movement, evidence or achievement kind")
        key = (agent_id, movement_id)
        if key in seen:
            raise ValueError("Duplicate agent movement award")
        seen.add(key)
        judges = award.get("judges")
        if not isinstance(judges, Mapping) or set(judges) != set(REQUIRED_JUDGES):
            raise ValueError("All four judge outcomes are required")
        if any(judges[judge] is not True for judge in REQUIRED_JUDGES):
            raise ValueError("Unapproved award cannot enter lifetime totals")
        if award.get("referee_approved") is not True:
            raise ValueError("Referee approval is required")
        totals[agent_id] += STAR_VALUES[kind]
    return sorted(
        ({"agent_id": agent_id, "name": str(agent["name"]), "achievement_stars": totals[agent_id]}
         for agent_id, agent in registry.items()),
        key=lambda row: (-row["achievement_stars"], row["name"].casefold(), row["agent_id"]),
    )
