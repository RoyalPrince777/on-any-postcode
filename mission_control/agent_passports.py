"""SMI specialist passports and seven bounded operating modes.

Taxonomy is descriptive: a passport never grants runtime permissions.
Animal Intelligence retains ownership of land intelligence.
"""
from __future__ import annotations

from dataclasses import dataclass

MODES = (
    "observe", "analyse", "plan", "coordinate", "build",
    "verify", "recover",
)

@dataclass(frozen=True)
class AgentPassport:
    agent_id: str
    intelligence: str
    domain: str
    role: str
    modes: tuple[str, ...] = MODES
    execution_authorised: bool = False


ANIMAL_ROLES = {
    "fox": ("land", "routing and alternative paths"),
    "octopus": ("marine", "cross-system orchestration"),
    "gorilla": ("land", "last-line defence"),
    "queen_bee": ("air", "distributed worker coordination"),
    "gyata": ("land", "sovereign command"),
    "lioness": ("land", "collective protection"),
    "tigress": ("land", "precision and discipline"),
    "shere_khan": ("land", "adversarial failure hunting"),
    "bagheera": ("land", "privacy and boundaries"),
    "owl": ("air", "wisdom and contextual judgement"),
    "eagle": ("air", "strategic vision"),
    "falcon": ("air", "speed and precision"),
    "bee": ("air", "coordination"),
    "elephant": ("land", "institutional memory"),
    "panther": ("land", "adaptation"),
    "spider": ("land", "dependency mapping"),
    "akela": ("land", "pack coordination"),
}

MATRIX_ROLES = {
    "neo": "engineering and adaptation",
    "morpheus": "mission strategy",
    "trinity": "operational collaboration",
    "oracle": "consequence analysis",
    "architect": "architecture",
    "keymaker": "authorised access and dependencies",
    "seraph": "trusted security boundaries",
    "tank": "runtime operations",
    "dozer": "infrastructure",
    "twins": "dual-path verification",
    "mouse": "edge-case hunting",
    "agent_smith": "adversarial testing",
    "brown": "adversarial testing",
    "jones": "adversarial testing",
    "johnson": "adversarial testing",
    "jackson": "adversarial testing",
    "thompson": "adversarial testing",
}


def agent_passport(agent_id: str) -> AgentPassport:
    """Return a stable identity and mode contract; never elevate permissions."""
    key = agent_id.strip().lower().replace(" ", "_") if isinstance(agent_id, str) else ""
    if key in ANIMAL_ROLES:
        domain, role = ANIMAL_ROLES[key]
        return AgentPassport(key, "animal", domain, role)
    if key in MATRIX_ROLES:
        return AgentPassport(key, "matrix", "systems", MATRIX_ROLES[key])
    raise ValueError("unknown_agent")


def passport_directory() -> tuple[AgentPassport, ...]:
    """Discover registered passports without exposing execution credentials."""
    return tuple(agent_passport(name) for name in (*ANIMAL_ROLES, *MATRIX_ROLES))


def agent_mode(agent_id: str, mode: str) -> dict[str, object]:
    """Describe a requested mode; this does not run the agent."""
    passport = agent_passport(agent_id)
    if mode not in MODES:
        raise ValueError("unknown_agent_mode")
    return {
        "agent": passport.agent_id,
        "intelligence": passport.intelligence,
        "domain": passport.domain,
        "mode": mode,
        "execution_authorised": False,
        "runtime_active": False,
    }


# Rank describes demonstrated capability, not seniority or permission.
RANKS = ("unverified", "learner", "capable", "proven", "expert", "master", "elite")
RANK_ARROWS = {"up": "↑", "same": "→", "down": "↓"}


def rank_movement(*, previous: str, current: str, evidence: tuple[str, ...] = ()) -> dict[str, object]:
    """Compare evidence-backed rank; never infer improvement from a vote or label."""
    if previous not in RANKS or current not in RANKS:
        raise ValueError("unknown_agent_rank")
    if not isinstance(evidence, tuple) or not all(
        isinstance(item, str) and item.strip() for item in evidence
    ):
        raise ValueError("invalid_rank_evidence")
    old, new = RANKS.index(previous), RANKS.index(current)
    direction = "up" if new > old else "down" if new < old else "same"
    if old != new and not evidence:
        raise ValueError("rank_change_requires_evidence")
    return {
        "previous": previous,
        "current": current,
        "direction": direction,
        "arrow": RANK_ARROWS[direction],
        "evidence": evidence,
        "execution_authorised": False,
    }
