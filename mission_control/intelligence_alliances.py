"""Founder-only SMI alliance board, separate from the canonical agent registry.

Fiction-inspired alliance roles are preserved as *design references*, not
production agents, third-party providers, or execution authorities.
No capability rating or career stars are inferred from membership.
"""
from __future__ import annotations

from typing import Any

from . import agents

# The recovered 14-person Mission: Impossible advisory design is *not* a
# registration or licensing claim. Existing agent passports stay unchanged.
MISSION_IMPOSSIBLE = (
    "Ethan Hunt", "Luther Stickell", "Benji Dunn", "Ilsa Faust",
    "William Brandt", "Grace", "Jane Carter", "Eugene Kittridge",
    "Alan Hunley", "Paris", "Nyah Nordoff-Hall", "Billy Baird",
    "Swanbeck", "Sean Ambrose",
)
TERMINATOR_CAPABILITIES = (
    "T-800 — resilience and protection",
    "T-1000 — adaptation and recovery",
    "T-X — diagnostics",
    "Rev-9 — coordination",
    "Cameron — human interaction",
    "John Connor — planning",
    "Sarah Connor — protection",
    "Kyle Reese — defensive planning",
)
PREDATOR_CAPABILITIES = (
    "Tracking and sensing", "Environmental awareness",
    "Survival analysis", "Defensive threat modelling",
)
TRANSFORMERS = ("Optimus Prime", "Bumblebee")
BATMAN = ("Batman", "Robin")


def get_founder_alliance_board() -> dict[str, Any]:
    """Expose recovered design alliances without granting agent status.

    The Jungle Book listing is projected from the canonical registry. The
    others are recorded *unranked* until a separately approved canonical
    identity and independently reviewed evidence exist.
    """
    jungle_book = tuple(
        {"name": str(agent["name"]), "agent_id": str(agent["agent_id"]),
         "ranking_eligible": True}
        for agent in agents.AGENT_REGISTRY
        if agent["family_id"] == "jungle_book"
    )
    def unregistered(names: tuple[str, ...]) -> tuple[dict[str, Any], ...]:
        return tuple(
            {"name": name, "agent_id": None, "ranking_eligible": False}
            for name in names
        )

    return {
        "scope": "founder_only_read_only",
        "status": "advisory_roster_reference",
        "human_authority": "Founder Final",
        "smi": {
            "name": "SMI",
            "kind": "intelligence_brain",
            "command_position": "Above specialist agent rankings",
            "career_ranking_eligible": False,
        },
        "mission_coordinator": {
            "name": "Captain ALL IN",
            "kind": "mission_coordination_role",
            "ranking": "Separate from canonical agent achievement totals",
        },
        "oversight": ("Guardian", "HRM Core"),
        "alliances": (
            {
                "id": "jungle_book", "name": "Jungle Book Intelligence",
                "status": "canonical_registered_family",
                "members": jungle_book,
            },
            {
                "id": "mission_impossible", "name": "Mission: Impossible Intelligence",
                "status": "recovered_advisory_design_only",
                "members": unregistered(MISSION_IMPOSSIBLE),
            },
            {
                "id": "terminator", "name": "Terminator Intelligence",
                "status": "existing_agent_capability_overlay_only",
                "members": unregistered(TERMINATOR_CAPABILITIES),
                "threat_models_not_agents": ("Skynet", "Legion"),
            },
            {
                "id": "predator", "name": "Predator Intelligence",
                "status": "existing_agent_capability_overlay_only",
                "members": unregistered(PREDATOR_CAPABILITIES),
            },
            {
                "id": "transformers", "name": "Transformers Intelligence",
                "status": "recovered_design_only",
                "members": unregistered(TRANSFORMERS),
            },
            {
                "id": "batman", "name": "Batman Intelligence",
                "status": "recovered_design_only",
                "members": unregistered(BATMAN),
            },
        ),
        "rank_policy": (
            "Existing approved agent rankings are unchanged. No invented "
            "rank numbers, no automatic stars, no duplicated passports; "
            "SMI is the coordinating brain, not a competing agent."
        ),
        "live_activation_claimed": False,
        "can_approve": False,
        "can_execute": False,
    }
