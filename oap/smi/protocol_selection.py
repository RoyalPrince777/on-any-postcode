"""Advisory protocol-specific SMI team selection; no authority or agent execution."""
from __future__ import annotations

from dataclasses import dataclass

# Named specialist roles are recommendations, not verified active agent processes.
PROTOCOL_TEAMS: dict[str, tuple[str, tuple[str, ...]]] = {
    "coordination": ("Captain ALL IN", ("Oracle", "Octopus", "Gyata")),
    "creation": ("NIRMATA", ("Architect", "Tigress", "Benji")),
    "execution": ("Neo", ("Trinity", "Tigress")),
    "stealth": ("Bagheera", ("Batman", "Luther", "Ilsa")),
    "guardian": ("Guardian", ("Seraph", "Gorilla", "Bagheera")),
    "adversarial": ("Shere Khan", ("Agent Smith", "Shark")),
    "pack": ("Akela", ("Octopus",)),
    "swarm": ("Queen Bee", ("Spider",)),
    "patterns": ("Octopus", ("Oracle", "Lucy", "Owl")),
    "dependencies": ("Spider", ("Architect", "Keymaker")),
    "recovery": ("Fox", ("Dozer", "Tank", "Benji")),
    "last_line_defence": ("Gorilla", ("Guardian", "Gyata")),
    "command": ("Gyata", ("Lioness", "Tigress")),
    "memory": ("Hathi", ("Elephant",)),
    "investigation": ("Batman", ("Robin", "Oracle", "Shere Khan")),
    "complex_missions": ("Ethan Hunt", ("Luther", "Benji", "Ilsa")),
    "matrix": ("Morpheus", ("Neo", "Trinity", "Oracle")),
    "identity": ("Seraph", ("Keymaker", "Guardian")),
    "verification": ("Tigress", ("The Twins", "Oracle")),
    "audit": ("HRM", ("Hathi", "Oracle")),
    "economics": ("MANSA", ("Owl", "Octopus", "Tigress")),
    "civic_rights": ("Batman", ("Nyah", "Ilsa", "Bagheera")),
    "language": ("NYANSA", ("Lucy", "Morpheus")),
    "science": ("NIRMATA", ("Lucy", "Octopus", "Tigress")),
    "threat_awareness": ("Shark", ("Eagle", "Owl", "Guardian")),
    "living_kernel": ("Architect", ("Neo", "Tank", "Guardian")),
    "deployment": ("Neo", ("Benji", "Trinity", "Dozer")),
    "green_gate": ("Independent verification", ("Tigress", "Oracle", "Guardian")),
}


@dataclass(frozen=True)
class ProtocolRecommendation:
    protocol: str
    lead: str | None
    specialists: tuple[str, ...]
    status: str
    advisory_only: bool = True
    grants_permissions: bool = False
    human_authority_final: bool = True


def recommend_protocol_team(protocol: str) -> ProtocolRecommendation:
    """Return advisory candidates; unknown input fails closed without fallback authority."""
    if not isinstance(protocol, str):
        return ProtocolRecommendation("", None, (), "UNRECOGNISED")
    key = protocol.strip().lower()
    team = PROTOCOL_TEAMS.get(key)
    if team is None:
        return ProtocolRecommendation(key, None, (), "UNRECOGNISED")
    return ProtocolRecommendation(key, team[0], team[1], "PROPOSED_UNVERIFIED")


@dataclass(frozen=True)
class MissionRoleRecommendation:
    """A bounded mission assignment proposal, never an execution grant."""

    mission: str
    protocol: str
    depth: str
    lead: str | None
    deputy: str | None
    specialists: tuple[str, ...]
    challenger: str | None
    verifier: str | None
    recovery: str | None
    status: str
    passport_verified: bool = False
    permissions_verified: bool = False
    evidence_verified: bool = False
    agent_execution_verified: bool = False
    grants_permissions: bool = False
    human_authority_final: bool = True


def recommend_mission_team(mission: str, protocol: str, depth: str = "AUTO") -> MissionRoleRecommendation:
    """Select advisory roles from existing mappings, with unknowns failing closed.

    AUTO uses a small team; it does not invent passport, performance or permission
    evidence. A separate authenticated registry/permission gate is required
    before any operational activation.
    """
    safe_mission = mission.strip() if isinstance(mission, str) else ""
    safe_depth = depth.upper().strip() if isinstance(depth, str) else ""
    selected = recommend_protocol_team(protocol)
    if not safe_mission or len(safe_mission) > 160 or safe_depth not in {"AUTO", "3", "7", "21", "FULL"} or selected.lead is None:
        return MissionRoleRecommendation(safe_mission[:160], selected.protocol, safe_depth, None, None, (), None, None, None, "UNRECOGNISED")
    pool = tuple(dict.fromkeys(selected.specialists))
    deputy = pool[0] if pool else None
    specialists = pool[1:] if safe_depth != "3" else ()
    # Reviewer and recovery roles are proposed only when their candidates exist.
    challenger = "Shere Khan" if safe_depth in {"AUTO", "7", "21", "FULL"} and selected.lead != "Shere Khan" else None
    verifier = "The Twins" if safe_depth in {"AUTO", "7", "21", "FULL"} else None
    recovery = "Fox" if selected.protocol in {"recovery", "deployment", "dependencies"} and selected.lead != "Fox" else None
    return MissionRoleRecommendation(safe_mission, selected.protocol, safe_depth, selected.lead, deputy, specialists, challenger, verifier, recovery, "PROPOSED_UNVERIFIED")


def check_mission_candidate_eligibility(
    agent_id: str, registry: object, *, required_permission: str = "ANALYSE"
) -> dict[str, object]:
    """Fail-closed read-only passport/permission eligibility for a candidate ID.

    Eligibility does not prove execution, performance, approval of a new role,
    or release readiness. Uses the existing RegistryEngine permission engine.
    """
    from oap.permissions import PermissionEngine

    if not isinstance(agent_id, str) or not agent_id.strip():
        return {"agent_id": "", "eligible": False, "reason": "INVALID_AGENT_ID", "grants_permissions": False}
    passport_lookup = getattr(registry, "passport", None)
    if not callable(passport_lookup):
        return {"agent_id": agent_id, "eligible": False, "reason": "REGISTRY_UNAVAILABLE", "grants_permissions": False}
    passport = passport_lookup(agent_id)
    if not isinstance(passport, dict) or passport.get("agent_id") != agent_id:
        return {"agent_id": agent_id, "eligible": False, "reason": "PASSPORT_NOT_FOUND", "grants_permissions": False}
    decision = PermissionEngine().authorize_agent(passport, required_permission=required_permission)
    return {
        "agent_id": agent_id,
        "eligible": bool(decision.allowed),
        "reason": decision.reason,
        "grants_permissions": False,
        "execution_verified": False,
        "performance_verified": False,
    }
