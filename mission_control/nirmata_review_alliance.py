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
    "neo": "Challenge assumptions and propose bounded solution routes within Matrix Intelligence.",
    "gyata": "Provide sovereign mission command and escalation without overriding Founder Final.",
    "queen_bee": "Coordinate authorised distributed work; Honey remains an internal protocol only.",
    "bee_swarm": "Perform assigned bounded worker tasks subject to existing permissions.",
    "akela": "Coordinate pack-level reliability, discipline and collective risk review.",
    "wolf_pack": "Inspect distributed teamwork, handoffs and continuity failure modes.",
}

NIRMATA_REVIEW_ROLES = MappingProxyType(_REVIEW_ROLES)

# Existing organism organs are oversight systems, never additional agents.
NIRMATA_OVERSIGHT_SYSTEMS = MappingProxyType({
    "living_kernel": "Control authorised execution lifecycle; never self-authorise.",
    "aegis": "Maintain defensive shielding and fail-closed security boundaries.",
})


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
        "oversight_systems": dict(NIRMATA_OVERSIGHT_SYSTEMS),
    }


def inspect_nirmata_blueprint(record: object) -> dict[str, object]:
    """Run bounded structural checks; do not represent them as specialist votes."""
    from collections.abc import Mapping

    from .nirmata_research import ANATOMY_LENSES, verify_blueprint_integrity

    findings: list[dict[str, str]] = []

    def flag(role: str, code: str) -> None:
        findings.append({"reviewer_role": role, "code": code})

    if not isinstance(record, Mapping):
        flag("agent_smith", "INVALID_RECORD")
    else:
        if not verify_blueprint_integrity(record):
            flag("agent_thompson", "INTEGRITY_NOT_VERIFIED")
        if record.get("evidence_status") != "unverified_references":
            flag("shark", "EVIDENCE_MISSING_OR_UNEXPECTED")
        if not record.get("sources"):
            flag("fox", "NO_SOURCE_REFERENCES")
        lenses = record.get("lenses")
        if not isinstance(lenses, list) or any(
            not isinstance(item, str) or item not in ANATOMY_LENSES for item in lenses
        ):
            flag("spider", "INVALID_RESEARCH_LENSES")
        if record.get("execution_authorised") is not False:
            flag("agent_jones", "EXECUTION_BOUNDARY_VIOLATION")
        if record.get("medical_diagnosis_authorised") is not False:
            flag("twin_one", "MEDICAL_BOUNDARY_VIOLATION")
        if record.get("identity_issuance_authorised") is not False:
            flag("twin_two", "IDENTITY_BOUNDARY_VIOLATION")

    return {
        "mission": "NIRMATA",
        "kind": "bounded_structural_review",
        "checks_executed": True,
        "scientific_validity_verified": False,
        "external_sources_verified": False,
        "specialist_votes_executed": 0,
        "earned_stars": None,
        "findings": findings,
        "passed": not findings,
    }
