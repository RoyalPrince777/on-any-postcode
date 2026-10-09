"""Read-only MATRIX council status adapter for existing Mission Control surfaces.

Does not register new routes, execute work, or change canonical War Room readiness.
"""
from __future__ import annotations

from .agent_passports import MODES, RANKS, passport_directory
from .matrix_system import MISSION_TEAMS, mission_council


def matrix_mission_status(mission: str) -> dict[str, object]:
    """Return one truthful status record suitable for an existing dashboard."""
    council = mission_council(mission)
    return {
        "system": "SMI MATRIX",
        "mission": mission,
        "command": council["command"],
        "captain": council["captain"],
        "coordinators": council["coordinators"],
        "recommended_lead": council["recommended_lead"],
        "specialists": council["specialists"],
        "modes": MODES,
        "ranks": RANKS,
        "votes_recorded": len(council["votes"]),
        "approved": council["approved"],
        "runtime_active": False,
        "production_ready": council["production_ready"],
        "blockers": council["blockers"],
    }


def matrix_registry_status() -> dict[str, object]:
    """Expose available contracts without suggesting deployed agents."""
    passports = passport_directory()
    return {
        "system": "SMI MATRIX",
        "registered_passports": len(passports),
        "mission_types": tuple(MISSION_TEAMS),
        "modes": MODES,
        "ranks": RANKS,
        "runtime_active": False,
        "execution_authorised": False,
        "production_ready": False,
    }
