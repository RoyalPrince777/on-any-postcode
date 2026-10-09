"""MATRIX mission leadership: Captain ALL IN and SMI remain accountable.

Nominations and votes are recommendations only. No agent can appoint itself,
terminate another agent, or grant runtime permissions.
"""
from __future__ import annotations

from dataclasses import dataclass

from .agent_passports import agent_passport

CAPTAIN = "captain_all_in"
COMMAND = "smi"


@dataclass(frozen=True)
class LeadershipDecision:
    mission: str
    recommended_lead: str
    supporting_agents: tuple[str, ...]
    nominations: tuple[str, ...]
    votes: tuple[tuple[str, str], ...]
    captain: str = CAPTAIN
    command: str = COMMAND
    approved: bool = False
    execution_authorised: bool = False


def recommend_lead(
    mission: str,
    eligible_agents: tuple[str, ...],
    *,
    nominations: tuple[str, ...] = (),
    votes: tuple[tuple[str, str], ...] = (),
) -> LeadershipDecision:
    """Recommend a mission lead, deterministically; no automatic appointment."""
    if not isinstance(mission, str) or not mission.strip():
        raise ValueError("invalid_mission")
    if not eligible_agents or len(set(eligible_agents)) != len(eligible_agents):
        raise ValueError("invalid_eligible_agents")
    for agent in eligible_agents:
        agent_passport(agent)
    for nominee in nominations:
        if nominee not in eligible_agents:
            raise ValueError("ineligible_nomination")
    voters: set[str] = set()
    counts = {agent: 0 for agent in eligible_agents}
    for voter, choice in votes:
        agent_passport(voter)
        if voter in voters:
            raise ValueError("duplicate_vote")
        if choice not in eligible_agents:
            raise ValueError("ineligible_vote")
        voters.add(voter)
        counts[choice] += 1
    # Ties resolve by original eligible order; nomination is a tie-breaker only.
    ordered = sorted(
        eligible_agents,
        key=lambda agent: (-counts[agent], -(agent in nominations), eligible_agents.index(agent)),
    )
    return LeadershipDecision(
        mission=mission,
        recommended_lead=ordered[0],
        supporting_agents=tuple(agent for agent in ordered if agent != ordered[0]),
        nominations=nominations,
        votes=votes,
    )


def propose_personnel_change(
    agent: str, action: str, *, evidence: tuple[str, ...] = ()
) -> dict[str, object]:
    """Request help, promotion, or termination review; never execute it."""
    passport = agent_passport(agent)
    if action not in {"help", "promotion", "termination_review"}:
        raise ValueError("invalid_personnel_action")
    if action in {"promotion", "termination_review"} and not evidence:
        raise ValueError("personnel_change_requires_evidence")
    if not isinstance(evidence, tuple) or not all(
        isinstance(item, str) and item.strip() for item in evidence
    ):
        raise ValueError("invalid_personnel_evidence")
    return {
        "agent": passport.agent_id,
        "action": action,
        "evidence": evidence,
        "status": "pending_smi_captain_review",
        "approved": False,
        "executed": False,
    }
