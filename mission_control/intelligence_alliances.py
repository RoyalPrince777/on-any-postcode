"""Founder-only SMI alliance board, separate from the canonical agent registry.

Fiction-inspired alliance roles are preserved as *design references*, not
production agents, third-party providers, or execution authorities.
No capability rating or career stars are inferred from membership.
"""
from __future__ import annotations

from collections.abc import Iterable, Mapping
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

# Dated advisory snapshot recovered from the Founder's earlier SMI discussions.
# Ratings are historical role-fit assessments, NOT career achievement awards.
# Some historical labels have no current passport and must stay unregistered.
HISTORICAL_TOP_21_2026_10_15: tuple[tuple[str, int], ...] = (
    ("Gyata", 7),
    ("Captain ALL IN", 7),
    ("Neo", 7),
    ("Nirmata", 7),
    ("Shere Khan", 7),
    ("Bagheera", 7),
    ("Oracle", 7),
    ("Octopus", 7),
    ("Owl", 7),
    ("Elephant", 7),
    ("Queen Bee", 7),
    ("Fox", 7),
    ("Panther", 6),
    ("Eagle", 6),
    ("Gorilla", 6),
    ("Tigress", 6),
    ("Lioness", 6),
    ("Spider", 6),
    ("Falcon", 6),
    ("Bee Swarm", 6),
    ("Keymaker", 6),
)


def _historical_top_21(career_stars: Mapping[str, int]) -> tuple[dict[str, Any], ...]:
    """Link dated references only to exact canonical agent names.

    Never register unknown historical names, infer aliases, or confer rank-based
    permissions/achievement stars.
    """
    by_name = {str(agent["name"]).casefold(): str(agent["agent_id"])
               for agent in agents.AGENT_REGISTRY}
    return tuple(
        {
            "rank": index,
            "name": name,
            "historical_rating": rating,
            "historical_rating_max": 7,
            "agent_id": by_name.get(name.casefold()),
            "registry_linked": name.casefold() in by_name,
            "career_stars": career_stars.get(by_name[name.casefold()], 0)
            if name.casefold() in by_name else None,
        }
        for index, (name, rating)
        in enumerate(HISTORICAL_TOP_21_2026_10_15, start=1)
    )


def get_founder_alliance_board(
    *, career_rankings: Iterable[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    """Expose recovered design alliances without granting agent status.

    The Jungle Book listing is projected from the canonical registry. The
    others are recorded *unranked* until a separately approved canonical
    identity and independently reviewed evidence exist.
    """
    stars_by_id = {
        str(row["agent_id"]): int(row["achievement_stars"])
        for row in career_rankings
    }
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
        "historical_top_21": {
            "as_of": "2026-10-15",
            "source": "Recovered Founder conversation snapshot; not runtime evidence",
            "rating_kind": "historical_advisory_role_fit",
            "separate_from_career_stars": True,
            "entries": _historical_top_21(stars_by_id),
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



def get_smi_command_alliances() -> dict[str, Any]:
    """Read-only projection of the Founder's requested existing SMI alliances.

    Registered passports are linked by exact canonical name; Matrix advisory
    members remain unregistered. Nothing in this projection activates agents,
    creates votes, grants permissions, or implies live swarm workers.
    """
    registered = {str(item["name"]): item for item in agents.AGENT_REGISTRY}
    matrix = {str(item["id"]): item for item in agents.MATRIX_ADVISORY_ALLIANCES}
    smith = matrix["smith_adversarial"]
    twins = matrix["matrix_twins"]

    def canonical(name: str, role: str) -> dict[str, Any]:
        agent = registered.get(name)
        return {
            "id": name.lower().replace(" ", "_"),
            "name": name,
            "role": str(agent["role"]) if agent else role,
            "family": str(agent["family_id"]) if agent else None,
            "passport_id": str(agent["agent_id"]) if agent else None,
            "passport_status": "registered" if agent else "advisory_only",
            "members": (name,),
            "allies": (),
            "directory_url": (
                "/mission/agents?family=" + str(agent["family_id"])
                if agent else None
            ),
            "runtime_verified": False,
            "execution_granted": False,
        }

    def matrix_alliance(row: dict[str, Any], name: str, role: str) -> dict[str, Any]:
        return {
            "id": str(row["id"]),
            "name": name,
            "role": role,
            "family": "matrix",
            "passport_id": None,
            "passport_status": "advisory_only",
            "members": tuple(str(member) for member in row["members"]),
            "allies": tuple(str(member) for member in row.get("allies", ())),
            "directory_url": None,
            "runtime_verified": False,
            "execution_granted": False,
        }

    return {
        "name": "SMI Command Center · Agent Alliances",
        "scope": "founder_private_read_only",
        "status": "advisory_projection_not_runtime_proof",
        "brain": "SMI",
        "members": (
            canonical("Shere Khan", "Adversarial threat review"),
            matrix_alliance(
                smith, "Agent Smiths", "Adversarial review and duplicate detection"
            ),
            canonical("Bagheera", "Protective strategy"),
            canonical("Octopus", "Cross-system coordination"),
            {
                "id": "queen_bee",
                "name": "Queen Bee",
                "role": "Conditional swarm and distributed worker coordination",
                "family": "insect_advisory",
                "passport_id": None,
                "passport_status": "advisory_only",
                "members": ("Queen Bee",),
                "allies": (),
                "directory_url": None,
                "runtime_verified": False,
                "execution_granted": False,
            },
            matrix_alliance(
                twins, "The Twins", "Alternative paths and contradiction review"
            ),
        ),
        "registered_agent_count_unchanged": len(agents.AGENT_REGISTRY),
        "independent_votes_proven": False,
        "workers_started": False,
        "guardian_hrm_required": True,
        "founder_final_required": True,
        "can_execute": False,
        "can_approve": False,
    }
