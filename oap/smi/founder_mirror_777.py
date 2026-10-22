"""Founder Mirror 777: pure, non-executing identity and passport projection.

No secrets, real document numbers, biometric data, or authentication claims.
This module does not create a second SMI brain or alter agent authority.
"""
from __future__ import annotations

from typing import Any

WHOLE_HUMAN_DIMENSIONS = (
    "mind", "body", "soul", "spirit", "heart", "awareness", "identity",
    "memory", "purpose", "energy", "intuition", "character", "wellbeing",
    "world", "safety", "voice", "face", "consciousness", "relationships",
    "foresight", "wisdom",
)

FOUNDER_ALIASES = ("N24-7", "Prince Nana Yaw", "Underground King")
RESTRICTED = "founder_private"
UNKNOWN = "unverified"


def founder_passport() -> dict[str, Any]:
    """Return a public-safe *internal design projection*, not a real identity card."""
    return {
        "kind": "internal_founder_passport",
        "issuer": "OAP SMI 777 (proposed)",
        "credential_status": "design_only_not_issued",
        "government_id": False,
        "primary_codename": "N24-7",
        "aliases": FOUNDER_ALIASES,
        "identity_source": "founder_stated_not_independently_verified",
        "brain_count": 1,
        "authority": "human_founder_final",
        "dimensions": WHOLE_HUMAN_DIMENSIONS,
        "privacy": RESTRICTED,
        "birth_certificate": {"status": UNKNOWN, "data": None},
        "permissions": {"can_impersonate_founder": False, "can_approve_as_founder": False},
        "operational_vpi": None,
    }


def agent_passport_projection(agent: dict[str, Any]) -> dict[str, Any]:
    """Read-only projection of an existing agent; never invent a new agent ID."""
    if not isinstance(agent, dict) or not agent.get("agent_id"):
        raise ValueError("Existing agent with an agent_id required")
    return {
        "kind": "internal_agent_passport_projection",
        "agent_id": agent["agent_id"],
        "name": agent.get("name"),
        "family_id": agent.get("family_id"),
        "status": agent.get("status", UNKNOWN),
        "origin_certificate": {
            "type": "software_origin_record",
            "created_at": agent.get("created_at"),
            "version": agent.get("version"),
        },
        "human_birth_certificate": False,
        "can_approve_as_founder": False,
    }


def founder_card_projection() -> dict[str, Any]:
    """Minimal internal card: no legal documents, aliases, or secret credentials."""
    passport = founder_passport()
    return {
        "kind": "internal_founder_card",
        "codename": passport["primary_codename"],
        "authority_label": "Founder Final (human only)",
        "whole_human_dimension_count": len(passport["dimensions"]),
        "credential_status": passport["credential_status"],
        "government_id": False,
        "auth_grant": False,
    }


def agent_registry_passport_projections(agents: object) -> tuple[dict[str, Any], ...]:
    """Project an existing registry without mutating it or inventing entries.

    Duplicate or missing IDs fail closed, including before a partial output.
    """
    if not isinstance(agents, (tuple, list)):
        raise ValueError("Existing registry sequence required")
    ids: set[str] = set()
    result: list[dict[str, Any]] = []
    for agent in agents:
        if not isinstance(agent, dict):
            raise ValueError("Registry entries must be dictionaries")
        agent_id = agent.get("agent_id")
        if not isinstance(agent_id, str) or not agent_id.strip() or agent_id in ids:
            raise ValueError("Missing or duplicate agent ID")
        ids.add(agent_id)
        result.append(agent_passport_projection(agent))
    return tuple(result)
