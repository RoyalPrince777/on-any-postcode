"""Read-only complementary intelligence review, without new agent identities.

A character's family membership and a species-inspired capability are separate.
These relationships are proposals for Founder review, not operational pairings.
"""
from __future__ import annotations

from .agents import AGENT_REGISTRY

REVIEW_PAIRS = (
    ("Shere Khan", "Tiger", "tiger"),
    ("Gyata", "Lioness", "lion"),
    ("Fox", "Foxy", "fox"),
    ("Bagheera", "Panther", "panther"),
)


def complementary_intelligence_review() -> dict:
    by_name = {str(agent["name"]).casefold(): agent for agent in AGENT_REGISTRY}
    pairs = []
    for left, right, capability in REVIEW_PAIRS:
        identities = []
        for name in (left, right):
            agent = by_name.get(name.casefold())
            identities.append({
                "name": name,
                "agent_id": agent["agent_id"] if agent else None,
                "family_id": agent["family_id"] if agent else None,
                "registered": agent is not None,
            })
        pairs.append({
            "capability": capability,
            "identities": identities,
            "pairing_verified": False,
            "distinct_roles_review_required": True,
        })
    return {
        "mode": "read_only",
        "pairs": pairs,
        "gender_based_role_assignment": False,
        "new_agent_ids_issued": False,
        "registry_mutated": False,
        "founder_final_required": True,
        "execution_authorised": False,
    }
