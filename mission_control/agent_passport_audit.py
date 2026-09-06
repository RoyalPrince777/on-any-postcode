"""Read-only War Room passport and position audit for OAP agents.

This module does not create agents, execute actions, write receipts, approve
changes, or change authority. It gives the Founder a safe audit board that keeps
Matrix Intelligence separate from the rest of the 78-agent registry while
showing which extra Matrix-style names are still candidate/passport-review items.
"""
from __future__ import annotations

from collections import Counter
from typing import Any

from . import agents

CORE_MATRIX_TEAM: tuple[dict[str, str], ...] = (
    {"name": "Neo", "position": "Kernel Sentinel / True Path Recovery Witness", "status": "registered"},
    {"name": "Morpheus", "position": "Truth Guide / Strategy Guide", "status": "registered"},
    {"name": "Trinity", "position": "Mind-Body-Soul Operations Coordinator", "status": "registered"},
    {"name": "Oracle", "position": "Foresight Analyst / Future Consequence", "status": "registered"},
    {"name": "Architect", "position": "Systems Designer / Structure", "status": "registered"},
    {"name": "Keymaker", "position": "Access Route Specialist / Permitted Paths", "status": "registered"},
    {"name": "Seraph", "position": "Security Reviewer / Boundary Protection", "status": "registered"},
)

MATRIX_EXTENDED_CANDIDATES: tuple[dict[str, str], ...] = (
    {"name": "Agent Smith", "position": "Integrity Challenger / Corruption Detector", "status": "passport_review"},
    {"name": "Tank", "position": "Pressure Shield / Defence Support", "status": "passport_review"},
    {"name": "Dozer", "position": "Blocker Clearing / Path Opening", "status": "passport_review"},
    {"name": "Switch", "position": "Mode Switch / State Change Checker", "status": "passport_review"},
    {"name": "Apoc", "position": "Failure Warning / Collapse Signal", "status": "passport_review"},
    {"name": "Ghost", "position": "Stealth Observer / Quiet Path Watcher", "status": "passport_review"},
    {"name": "Niobe", "position": "Route Captain / Movement Command", "status": "passport_review"},
    {"name": "Twinz", "position": "Dual-Path Mirror / Parallel Consistency Check", "status": "passport_review"},
)

REMOVED_MATRIX_CANDIDATES: tuple[dict[str, str], ...] = (
    {"name": "Cypher", "reason": "Founder removed candidate after War Room duplicate-risk review", "status": "removed_by_founder"},
    {"name": "Mouse", "reason": "Founder removed from active Matrix review unless a future micro-detail role is proven necessary; Ant/Bee/Spider cover stronger animal-intelligence alternatives", "status": "removed_unless_needed"},
)

WAR_ROOM_PASSPORT_CHECKS: tuple[str, ...] = (
    "agent_id present and unique",
    "name present and canonical",
    "family_id assigned to one family only",
    "position/role does not duplicate a system organ",
    "Soul-Mind-Body present",
    "Guardian assigned",
    "Human Authority cannot be bypassed",
    "execution disabled unless a separate approved Builder path exists",
    "HRM audit required",
    "SMI/NEXUS/OASIS/War Room remain systems, not agents",
)

POSITION_LOCKS: dict[str, str] = {
    "SMI": "Brain / one intelligence brain; not an agent",
    "NEXUS": "Neck + nervous bridge; not an agent",
    "OASIS": "Human experience / environment; not an agent",
    "War Room": "Strategic chamber; not an agent",
    "Guardian": "Protective gate; not an agent",
    "HRM Core": "Memory; not an agent",
    "Neo": "Matrix Kernel Sentinel close to SMI and Nexus",
    "Agent Smith": "Candidate final integrity challenger; not yet registered as Matrix core",
    "Twinz": "Candidate dual-path mirror for parallel consistency checks",
    "Mouse": "Removed unless needed; may only return as Animal Intelligence micro-detail scout after War Room proof",
    "Cypher": "Removed Matrix candidate; not available for passport review",
}


def _registered_by_family() -> dict[str, int]:
    counts = Counter(str(agent["family_id"]) for agent in agents.AGENT_REGISTRY)
    return dict(sorted(counts.items()))


def _matrix_registered_names() -> tuple[str, ...]:
    return tuple(
        str(agent["name"])
        for agent in agents.AGENT_REGISTRY
        if agent["family_id"] == "matrix"
    )


def passport_audit() -> dict[str, Any]:
    """Return a safe War Room passport audit without mutating the registry."""

    registry_names = tuple(str(agent["name"]) for agent in agents.AGENT_REGISTRY)
    duplicate_names = tuple(
        name for name, count in Counter(registry_names).items() if count > 1
    )
    system_names = {system["name"] for system in agents.ORGANISM_NON_AGENT_SYSTEMS}
    agent_names = set(registry_names)
    system_agent_collisions = tuple(sorted(system_names & agent_names))
    matrix_names = _matrix_registered_names()
    missing_core_matrix = tuple(
        item["name"] for item in CORE_MATRIX_TEAM if item["name"] not in matrix_names
    )
    candidate_already_registered = tuple(
        item["name"]
        for item in MATRIX_EXTENDED_CANDIDATES
        if item["name"] in matrix_names
    )

    return {
        "name": "War Room Agent Passport Audit",
        "mode": "read_only_founder_review",
        "agent_count_target": agents.LOCKED_AGENT_COUNT,
        "agent_count_current": len(agents.AGENT_REGISTRY),
        "families": agents.INTELLIGENCE_FAMILIES,
        "worlds": agents.INTELLIGENCE_WORLDS,
        "registered_by_family": _registered_by_family(),
        "matrix_core": {
            "expected_count": 7,
            "registered_count": len(matrix_names),
            "registered_names": matrix_names,
            "team": CORE_MATRIX_TEAM,
            "missing_core": missing_core_matrix,
            "status_light": "green" if len(matrix_names) == 7 and not missing_core_matrix else "orange",
        },
        "matrix_extended": {
            "status_light": "yellow",
            "meaning": "Candidate layer for War Room passport review; not counted as registered Matrix core yet.",
            "candidates": MATRIX_EXTENDED_CANDIDATES,
            "removed_candidates": REMOVED_MATRIX_CANDIDATES,
            "already_registered_as_core": candidate_already_registered,
        },
        "position_locks": POSITION_LOCKS,
        "war_room_checks": WAR_ROOM_PASSPORT_CHECKS,
        "collisions": {
            "duplicate_agent_names": duplicate_names,
            "system_agent_name_collisions": system_agent_collisions,
            "status_light": "green" if not duplicate_names and not system_agent_collisions else "red",
        },
        "guardian": {
            "pass": not system_agent_collisions,
            "reason": "Systems/organs must not be counted as agents or authority holders.",
        },
        "green_gate": {
            "pass": False,
            "reason": "Extended candidates need passport entries, tests, HRM receipt and Founder approval before full green.",
        },
        "founder_decision_needed": True,
    }


def war_room_recommendation() -> dict[str, Any]:
    """Return the next safe recommendation for the Founder."""

    audit = passport_audit()
    return {
        "recommendation": "Keep Matrix Core at 7; audit the extended Matrix candidates separately before adding passports. Cypher is removed and Mouse is removed unless a future Animal Intelligence micro-detail role is proven necessary.",
        "decision_options": (
            "Hold Matrix Core at 7 and keep candidates in review",
            "Create passports for selected Matrix Extended candidates after War Room review",
            "Keep Mouse removed unless Ant/Bee/Spider cannot cover the micro-detail scout role",
            "Keep Cypher removed unless Founder re-approves a safer replacement role",
            "Reject any candidate that duplicates an existing family or system organ",
        ),
        "audit": audit,
    }
