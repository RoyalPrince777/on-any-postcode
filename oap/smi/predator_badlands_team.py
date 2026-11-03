"""Badlands-inspired teamwork model: advisory proposals, not autonomous agents.

Film-inspired roles preserve contrasting perspectives. All observations must be
supplied explicitly; this module never acquires sensors or invokes tools.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class TeamPerspective:
    character: str
    responsibility: str
    authority: str = "advisory"


BADLANDS_TEAM: tuple[TeamPerspective, ...] = (
    TeamPerspective("dek", "Propose adaptive recovery approaches."),
    TeamPerspective("thia", "Explain evidence, constraints and cooperation options."),
    TeamPerspective("bud", "Interpret explicitly supplied biological context only."),
    TeamPerspective("kwei", "Assess protective continuity and rollback options."),
    TeamPerspective("tessa", "Challenge assumptions through defensive analysis."),
    TeamPerspective("njohrr", "Examine authority conflicts without granting authority."),
)


def review_plan(evidence: dict[str, str] | None) -> dict[str, object]:
    """Return a bounded review plan; unknown evidence never implies readiness."""
    if not isinstance(evidence, dict) or not evidence:
        return {"ready": False, "reason": "NO_VERIFIED_EVIDENCE", "roles": ()}
    if any(not isinstance(key, str) or not isinstance(value, str) or not value.strip()
           for key, value in evidence.items()):
        return {"ready": False, "reason": "INVALID_EVIDENCE", "roles": ()}
    return {
        "ready": False,
        "reason": "HUMAN_REVIEW_REQUIRED",
        "roles": tuple(item.character for item in BADLANDS_TEAM),
    }
