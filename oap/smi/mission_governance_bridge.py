"""Read-only SMI mission governance bridge; never authorises execution.

This bridge produces an inspectable review record from existing registry and
permission checks. Guardian and HRM evidence must be supplied by their actual
governed services; caller assertions cannot activate a team.
"""
from __future__ import annotations

from oap.smi.protocol_selection import (
    recommend_mission_team,
    screen_mission_team_candidates,
)


def review_mission_candidates(
    mission: str,
    protocol: str,
    registry: object,
    *,
    agent_ids: dict[str, str] | None = None,
    depth: str = "AUTO",
) -> dict[str, object]:
    """Return a fail-closed, non-authorising selection review record."""
    recommendation = recommend_mission_team(mission, protocol, depth)
    if recommendation.status != "PROPOSED_UNVERIFIED":
        return {
            "mission": recommendation.mission,
            "protocol": recommendation.protocol,
            "status": "REJECTED_INVALID_RECOMMENDATION",
            "candidates": {},
            "all_eligible": False,
            "guardian_review_verified": False,
            "hrm_audit_verified": False,
            "founder_final_required": True,
            "grants_permissions": False,
            "agent_execution_verified": False,
        }
    screening = screen_mission_team_candidates(
        recommendation, registry, agent_ids=agent_ids
    )
    return {
        **screening,
        "status": "FOUNDER_REVIEW_REQUIRED"
        if screening["all_eligible"]
        else "REJECTED_INELIGIBLE_CANDIDATES",
        "guardian_review_verified": False,
        "hrm_audit_verified": False,
        "founder_final_required": True,
        "grants_permissions": False,
        "agent_execution_verified": False,
    }
