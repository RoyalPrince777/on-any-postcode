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

ANIMAL_REVIEW_CANDIDATES: tuple[dict[str, str], ...] = (
    {"name": "Cat", "team": "land", "position": "Silent Detail Hunter / Independent Pattern Watcher", "status": "passport_review"},
    {"name": "Tygress", "team": "land", "position": "Focused Huntress / Precision Pressure Watch", "status": "passport_review"},
    {"name": "Lioness", "team": "land", "position": "Protective Pride Strategist / Family Pack Guardian", "status": "passport_review"},
    {"name": "Gorilla", "team": "land", "position": "Strength Steward / Heavy Protection and Calm Power", "status": "passport_review"},
    {"name": "Shark", "team": "water", "position": "Deep Risk Hunter / Hidden Threat Scanner", "status": "passport_review"},
)

DOG_REVIEW_CANDIDATES: tuple[dict[str, str], ...] = (
    {"name": "Shepherd Dog", "team": "pack", "position": "Pack Guide / Loyalty Guardian / Route Discipline", "status": "passport_review"},
    {"name": "Bloodhound", "team": "pack", "position": "Evidence Trail Finder / Source Scent Tracker", "status": "passport_review"},
    {"name": "Collie", "team": "pack", "position": "Fast Coordination / Task Discipline", "status": "passport_review"},
    {"name": "Pitbull", "team": "pack", "position": "Pressure Courage / Loyal Resilience Watch", "status": "controlled_review"},
    {"name": "Rottweiler", "team": "pack", "position": "Boundary Confidence / Protective Presence", "status": "controlled_review"},
)

JUNGLE_BOOK_REVIEW_CANDIDATES: tuple[dict[str, str], ...] = (
    {"name": "Baloo", "position": "Calm Mentor / Wellbeing and Recovery Guide", "status": "passport_review"},
    {"name": "King Louie", "position": "Influence Watch / Crowd Energy and Ego Pressure Review", "status": "passport_review"},
    {"name": "Bandar Log", "position": "Noise Swarm / Distraction Pattern Detector", "status": "passport_review"},
)

REMOVED_MATRIX_CANDIDATES: tuple[dict[str, str], ...] = (
    {"name": "Cypher", "reason": "Founder removed candidate after War Room duplicate-risk review", "status": "removed_by_founder"},
)

REMOVED_ANIMAL_CANDIDATES: tuple[dict[str, str], ...] = (
    {"name": "Mouse", "reason": "Founder removed completely after Animal Intelligence duplicate review", "status": "removed_by_founder"},
    {"name": "Guard Dog", "reason": "Founder removed generic dog role because it duplicated Guardian", "status": "removed_by_founder"},
)

WAR_ROOM_BUTTONS: tuple[dict[str, str], ...] = (
    {"button": "🧠", "name": "SMI First Look", "signal": "🟣", "purpose": "classify role, family, team, risk and review cycle"},
    {"button": "🕶️", "name": "Neo True Path", "signal": "🔵", "purpose": "check true path, failure recovery and fake-green drift"},
    {"button": "🐅", "name": "Shere Khan Pressure", "signal": "🟠", "purpose": "pressure-test weakness, ego, aggression and bypass risk"},
    {"button": "🐆", "name": "Bagheera Wisdom", "signal": "🟢", "purpose": "check calm judgement, protection, balance and purpose"},
    {"button": "🕶️", "name": "Agent Smith Duplicate", "signal": "🟡", "purpose": "detect duplicate roles, corruption, copycat logic and false order"},
    {"button": "🛡️", "name": "Guardian + Green Gate", "signal": "🟢/🔴/🔒", "purpose": "check safety boundaries and proof before green"},
    {"button": "👑", "name": "Founder Final", "signal": "👑", "purpose": "Founder decides approve, hold, sharpen, remove or send back"},
)

REVIEW_OUTCOME_TEMPLATE: dict[str, str] = {
    "agent": "Name of agent or candidate",
    "role": "One-line canonical role",
    "agreed": "Where SMI, Neo, Shere Khan, Bagheera, Agent Smith, Guardian and Green Gate agree",
    "disagreed": "Where judges disagree or where role needs argument",
    "recommended_signal": "🟢 pass review / 🟡 hold-sharpen / 🟠 orange block / 🔴 red block / 🔒 full green locked",
    "argument": "Short War Room reason that proves why the verdict is correct",
    "verdict": "Pass Review, Hold/Sharpen, Orange Block, Red Block, or Founder Final needed",
    "rating": "⭐ to ⭐⭐⭐⭐⭐⭐⭐",
    "full_green": "🔒 NO until passport, tests, HRM receipt, Green Gate proof and Founder final approval",
    "founder_final": "👑 needed",
}

WAR_ROOM_STAGE_RULES: dict[str, str] = {
    "7x_low": "simple naming or low-risk role check",
    "14x_medium": "duplicate, structure or team-placement review",
    "21_3x7_high": "safety, pressure, protection, authority, activation, public/private or Green Gate review",
}

WAR_ROOM_SPEECH_LOCK: dict[str, str] = {
    "SMI": "I check role, family, risk and stage. This is review only, not full green.",
    "Neo": "I check the true path. If the role drifts, it goes back to review.",
    "Shere Khan": "I pressure-test weakness. Strength without boundaries becomes danger.",
    "Bagheera": "I check wisdom, restraint, protection and balance.",
    "Agent Smith": "I detect duplicates, corruption, copycat roles and false order.",
    "Guardian": "I check safety. No harm, no tracking, no authority takeover, no private leak.",
    "Green Gate": "Review can pass. Full green needs passport, tests, receipt, proof and Founder final.",
    "Founder": "Founder Authority decides: approve, hold, sharpen, remove or send back.",
}

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
    "Cat": "Animal Intelligence candidate; silent detail hunter and independent pattern watcher",
    "Tygress": "Animal Intelligence candidate; focused huntress and precision pressure watch",
    "Lioness": "Animal Intelligence candidate; protective pride strategist and family pack guardian",
    "Gorilla": "Animal Intelligence candidate; calm strength and heavy protection with restraint",
    "Shark": "Water Intelligence candidate inside Animal Intelligence; deep hidden-risk scanner",
    "Shepherd Dog": "Dog Intelligence candidate; moving pack guide and route discipline",
    "Bloodhound": "Dog Intelligence candidate; evidence trail finder and source scent tracker",
    "Collie": "Dog Intelligence candidate; fast coordination and task discipline",
    "Pitbull": "Dog Intelligence candidate; loyal courage under pressure with no attack framing",
    "Rottweiler": "Dog Intelligence candidate; boundary presence warning, not Guardian authority",
    "Baloo": "Jungle Book Intelligence candidate; calm mentor for wellbeing, recovery and grounded support",
    "King Louie": "Jungle Book Intelligence candidate; influence watch for crowd energy, ego pressure and imitation risk",
    "Bandar Log": "Jungle Book Intelligence candidate; noise swarm detector for distraction, copycat chatter and unstable group signal",
    "Cypher": "Removed Matrix candidate; not available for passport review",
    "Mouse": "Removed completely by Founder decision",
    "Guard Dog": "Removed by Founder decision; generic role duplicated Guardian",
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


def _candidate_names(items: tuple[dict[str, str], ...]) -> tuple[str, ...]:
    return tuple(str(item["name"]) for item in items)


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
    animal_candidate_already_registered = tuple(
        item["name"]
        for item in ANIMAL_REVIEW_CANDIDATES
        if item["name"] in registry_names
    )
    dog_candidate_already_registered = tuple(
        item["name"]
        for item in DOG_REVIEW_CANDIDATES
        if item["name"] in registry_names
    )
    jungle_book_candidate_already_registered = tuple(
        item["name"]
        for item in JUNGLE_BOOK_REVIEW_CANDIDATES
        if item["name"] in registry_names
    )

    return {
        "name": "War Room Agent Passport Audit",
        "mode": "read_only_founder_review",
        "agent_count_target": agents.LOCKED_AGENT_COUNT,
        "agent_count_current": len(agents.AGENT_REGISTRY),
        "families": agents.INTELLIGENCE_FAMILIES,
        "worlds": agents.INTELLIGENCE_WORLDS,
        "registered_by_family": _registered_by_family(),
        "war_room_buttons": WAR_ROOM_BUTTONS,
        "review_outcome_template": REVIEW_OUTCOME_TEMPLATE,
        "stage_rules": WAR_ROOM_STAGE_RULES,
        "speech_lock": WAR_ROOM_SPEECH_LOCK,
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
        "animal_review": {
            "status_light": "yellow",
            "meaning": "Animal Intelligence candidate layer for War Room passport review; not counted as registered agents yet.",
            "candidates": ANIMAL_REVIEW_CANDIDATES,
            "already_registered": animal_candidate_already_registered,
        },
        "dog_review": {
            "status_light": "yellow",
            "meaning": "Dog Intelligence candidate pack inside Animal Intelligence review; not counted as registered agents yet.",
            "candidates": DOG_REVIEW_CANDIDATES,
            "already_registered": dog_candidate_already_registered,
        },
        "jungle_book_review": {
            "status_light": "yellow",
            "meaning": "Jungle Book Intelligence candidate layer for War Room passport review; not counted as registered agents yet.",
            "candidates": JUNGLE_BOOK_REVIEW_CANDIDATES,
            "already_registered": jungle_book_candidate_already_registered,
        },
        "animal_removed": REMOVED_ANIMAL_CANDIDATES,
        "position_locks": POSITION_LOCKS,
        "war_room_checks": WAR_ROOM_PASSPORT_CHECKS,
        "collisions": {
            "duplicate_agent_names": duplicate_names,
            "system_agent_name_collisions": system_agent_collisions,
            "candidate_name_sets": {
                "matrix_extended": _candidate_names(MATRIX_EXTENDED_CANDIDATES),
                "animal_review": _candidate_names(ANIMAL_REVIEW_CANDIDATES),
                "dog_review": _candidate_names(DOG_REVIEW_CANDIDATES),
                "jungle_book_review": _candidate_names(JUNGLE_BOOK_REVIEW_CANDIDATES),
            },
            "status_light": "green" if not duplicate_names and not system_agent_collisions else "red",
        },
        "guardian": {
            "pass": not system_agent_collisions,
            "reason": "Systems/organs must not be counted as agents or authority holders.",
        },
        "green_gate": {
            "review_green": True,
            "full_system_green": False,
            "reason": "Review structure can pass, but candidates need passport entries, tests, HRM receipt and Founder approval before full green.",
        },
        "founder_decision_needed": True,
    }


def war_room_recommendation() -> dict[str, Any]:
    """Return the next safe recommendation for the Founder."""

    audit = passport_audit()
    return {
        "recommendation": "Use the upgraded War Room decision format for every candidate: agreed, disagreed, recommended signal, argument, verdict, rating, full-green lock and Founder final. Keep Matrix Core at 7; audit all extended, animal, dog and Jungle Book candidates separately before adding passports.",
        "decision_options": (
            "Pass review when judges agree the role is clear and bounded",
            "Hold/sharpen when role is useful but too close to another agent",
            "Orange block when role is noisy, risky or duplicated right now",
            "Red block when role breaks safety, authority or duplicate rules",
            "Keep full system green locked until passport, tests, HRM receipt, Green Gate proof and Founder final",
            "Reject any candidate that duplicates an existing family or system organ",
        ),
        "audit": audit,
    }
