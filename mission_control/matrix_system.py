"""First-party MATRIX specialist routing contract; no autonomous execution authority."""

from __future__ import annotations

from dataclasses import dataclass

SPECIALISTS = {
    "fox": "routing",
    "octopus": "integration",
    "neo": "engineering",
    "dozer": "infrastructure",
    "morpheus": "strategy",
    "oracle": "consequence_analysis",
    "architect": "architecture",
    "keymaker": "access_dependencies",
    "seraph": "security",
    "tank": "operations",
    "twins": "dual_path_verification",
    "mouse": "edge_cases",
    "agent_smith": "adversarial",
    "gorilla": "last_line_defence",
    "queen_bee": "distributed_workers",
}

MISSION_TEAMS = {
    "database_migration": ("fox", "octopus", "architect", "dozer", "keymaker", "twins", "gorilla"),
    "public_endpoint": ("fox", "octopus", "neo", "seraph", "mouse", "agent_smith"),
    "runtime_recovery": ("fox", "octopus", "tank", "dozer", "gorilla"),
    "distributed_work": ("fox", "octopus", "queen_bee", "tank"),
}


@dataclass(frozen=True)
class MissionDecision:
    mission: str
    specialists: tuple[str, ...]
    permitted_to_execute: bool
    production_ready: bool
    evidence: tuple[str, ...]
    blockers: tuple[str, ...]


def route_mission(mission: str, *, evidence: tuple[str, ...] = ()) -> MissionDecision:
    """Select bounded roles without granting execution or production authority."""
    if mission not in MISSION_TEAMS:
        raise ValueError("unknown_matrix_mission")
    if not isinstance(evidence, tuple) or not all(
        isinstance(item, str) and item.strip() for item in evidence
    ):
        raise ValueError("invalid_matrix_evidence")
    return MissionDecision(
        mission=mission,
        specialists=MISSION_TEAMS[mission],
        permitted_to_execute=False,
        production_ready=False,
        evidence=evidence,
        blockers=("human_authorisation_required", "runtime_verification_required"),
    )


def mission_council(
    mission: str,
    *,
    nominations: tuple[str, ...] = (),
    votes: tuple[tuple[str, str], ...] = (),
    evidence: tuple[str, ...] = (),
) -> dict[str, object]:
    """Join routing, passports and leadership in one non-executing mission record."""
    from .agent_passports import agent_passport
    from .matrix_leadership import recommend_lead

    route = route_mission(mission, evidence=evidence)
    # FOX and OCTOPUS are peers in coordination, not competing mission candidates
    # unless explicitly selected through a separate authorised governance change.
    eligible = tuple(agent for agent in route.specialists if agent not in {"fox", "octopus"})
    leadership = recommend_lead(mission, eligible, nominations=nominations, votes=votes)
    return {
        "mission": mission,
        "command": leadership.command,
        "captain": leadership.captain,
        "coordinators": ("fox", "octopus"),
        "recommended_lead": leadership.recommended_lead,
        "specialists": tuple(
            {"agent": agent, "intelligence": agent_passport(agent).intelligence,
             "domain": agent_passport(agent).domain}
            for agent in route.specialists
        ),
        "votes": leadership.votes,
        "nominations": leadership.nominations,
        "evidence": route.evidence,
        "approved": False,
        "permitted_to_execute": False,
        "production_ready": False,
        "blockers": route.blockers,
    }
