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
