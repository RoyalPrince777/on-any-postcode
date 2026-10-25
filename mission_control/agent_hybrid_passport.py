"""Read-only OAP Hybrid Agent Passport projection.

Identity comes exclusively from the existing canonical registry. This module
does not issue credentials, register agents, authenticate callers or grant access.
The caller MUST enforce Founder authentication before using founder_passport().
"""
from __future__ import annotations

from .agents import AGENT_REGISTRY


def _find_agent(agent_id: str):
    if not isinstance(agent_id, str) or not agent_id:
        return None
    return next((agent for agent in AGENT_REGISTRY if agent["agent_id"] == agent_id), None)


def public_passport(agent_id: str) -> dict | None:
    """Public-safe identity projection, not a claim of certification."""
    agent = _find_agent(agent_id)
    if agent is None:
        return None
    return {
        "agent_id": agent["agent_id"],
        "name": agent["name"],
        "family_id": agent["family_id"],
        "role": agent["role"],
        "passport_verified": False,
        "runtime_verified": False,
    }


def founder_passport(agent_id: str, *, founder_authorised: bool = False) -> dict | None:
    """Fail closed unless an upstream authenticated Founder gate authorises access."""
    if founder_authorised is not True:
        return None
    agent = _find_agent(agent_id)
    if agent is None:
        return None
    return {
        **public_passport(agent_id),
        "permissions": tuple(agent.get("permissions", ())),
        "restrictions": tuple(agent.get("restrictions", ())),
        "founder_final_required": True,
        "execution_authorised": False,
        "credential_presented": False,
        "mission_stars": None,
        "mission_stars_status": "unverified",
    }
