"""Bounded NIRMATA review assignments; roles are not new agents or executed votes."""

from __future__ import annotations

from types import MappingProxyType

_REVIEW_ROLES = {
    "fox": "Find safe recovery routes for failed dependencies and checks.",
    "octopus": "Coordinate existing integration dependencies without executing changes.",
    "spider": "Trace dependency edges and cascading failure exposure.",
    "shark": "Prioritise critical weaknesses by evidenced impact.",
    "agent_smith": "Challenge assumptions and the completeness of adversarial review.",
    "agent_brown": "Detect duplicated capability and conflicting logic.",
    "agent_jones": "Inspect permission and security boundary violations.",
    "agent_johnson": "Examine architecture and dependency failure modes.",
    "agent_jackson": "Examine recovery and continuity failure modes.",
    "agent_thompson": "Audit evidence integrity and unsupported claims.",
    "twin_one": "Examine hidden paths and boundary transitions.",
    "twin_two": "Examine state transitions and race conditions.",
}

NIRMATA_REVIEW_ROLES = MappingProxyType(_REVIEW_ROLES)


def nirmata_review_plan() -> dict[str, object]:
    """Return advisory assignments only; never imply that reviews ran."""
    return {
        "mission": "NIRMATA",
        "mode": "advisory_only",
        "execution_authorised": False,
        "reviews_executed": 0,
        "verified_votes": 0,
        "earned_stars": None,
        "roles": dict(NIRMATA_REVIEW_ROLES),
    }
