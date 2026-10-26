"""Review-only SMI specialist extensions: military, executive, command-tree, chess,
Guardian-linked safety and historical imperial research.

No real government affiliations, military command, emperor identity, personal
surveillance, emergency dispatch, autonomous votes or new canonical passports.
This module NEVER adds to the preserved 78-agent registry.
"""
from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from typing import Any

# Public official British Army rank reference; these are *not* agent passports.
# https://www.army.mod.uk/learn-and-explore/ranks/
UK_ARMY_RANK_REFERENCE = {
    "soldier": (
        "Private", "Lance Corporal", "Corporal", "Sergeant",
        "Staff Sergeant", "Warrant Officer Class Two",
        "Warrant Officer Class One",
    ),
    "officer": (
        "Officer Cadet", "Second Lieutenant", "Lieutenant", "Captain",
        "Major", "Lieutenant Colonel", "Colonel", "Brigadier",
        "Major General", "Lieutenant General", "General", "Field Marshal",
    ),
}
RANK_REFERENCE_NOTE = (
    "Soldier and officer hierarchies are separate tracks; Officer Cadet "
    "is an officer-training designation and Field Marshal is normally honorary."
)

# Distinct research teams; 'military' reuses the previous draft family's key.
EXTENDED_FAMILY_ROWS = [["military","Defence Intelligence Research","civilisation"],["presidential","Presidential Intelligence Research","civilisation"],["command_tree","Command Relationship Matrix and Family Tree","civilisation"],["chess","Chess Role and Strategy Research","civilisation"],["guardian_review","Guardian Advisory Safety Specialists","life"],["imperial","Imperial Governance and History Research","civilisation"]]
# Functional name, family key, bounded advisory research task, temperament.
EXTENDED_AGENT_ROWS = [["Military Chain-of-Command Analyst","military","Military rank and lawful escalation review","disciplined"],["Land Defence Research Analyst","military","Public-source land-defence resilience analysis, without targeting","grounded"],["Naval Maritime Security Analyst","military","Maritime infrastructure and civilian safety risk analysis","watchful"],["Airspace Defence Research Analyst","military","Civilian airspace risk, resilience and verified advisories","precise"],["Space Systems Defence Risk Analyst","military","Satellite reliance, infrastructure hazards and continuity research","methodical"],["Military Logistics Resilience Analyst","military","Supply continuity, humanitarian logistics and recovery planning","practical"],["Military Medical Support Researcher","military","Non-clinical casualty-care policy and emergency referral research","compassionate"],["Military Humanitarian Law Reviewer","military","Public international humanitarian law and protective compliance review","principled"],["Presidential Intelligence Source Coordinator","presidential","Public-source provenance for an executive intelligence briefing","impartial"],["Executive Continuity Research Analyst","presidential","Constitutional continuity and government-resilience research","deliberate"],["Presidential Protective Intelligence Analyst","presidential","Public protective-security principles, without personal tracking","vigilant"],["Organisational Family Tree Analyst","command_tree","Document OAP research family membership and reporting relationships without real-world rank claims","systematic"],["Cross-Branch Reporting Line Auditor","command_tree","Check reporting-line boundaries and preserve Founder and Guardian authority","exact"],["Chess King and Queen Role Analyst","chess","Compare king safety and queen mobility as chess roles, never real governing powers","creative"],["Chess Rook Bishop and Knight Analyst","chess","Study distinct chess-piece movement and complementary tactics","patient"],["Chess Pawn Structure Analyst","chess","Study pawn structure and promotion as game strategy without human rank claims","scrupulous"],["Guardian Consent Audit Analyst","guardian_review","Verify consent evidence without becoming Guardian authority","careful"],["Guardian Incident Escalation Analyst","guardian_review","Safety incident classification and official-service referral research","steady"],["Guardian Recovery Evidence Reviewer","guardian_review","Review whether safeguards and recovery are proved after incidents","methodical"],["Imperial Constitutional Researcher","imperial","Compare documented constitutional roles and limits of emperors","balanced"],["Imperial History and Succession Researcher","imperial","Research imperial history and documented succession rules","historical"]]

# This is a governance/research family tree, NOT the fictional Matrix film family.
# Real presidents and emperors do not report to SMI: they are comparison topics.
# Chess piece roles are a game taxonomy, not real-world ranks.
CHESS_POSITION_ROLES = ("King", "Queen", "Rook", "Bishop", "Knight", "Pawn")
COMPARATIVE_OFFICES = {
    "presidential": ("President", "Executive advisers", "Intelligence briefers"),
    "imperial": ("Emperor", "Imperial office", "Succession and constitutional research"),
    "military": ("Soldier rank track", "Officer rank track"),
}
COMMAND_FAMILY_BRANCHES = (
    {"key": "policing", "title": "Police, CID and security", "families": (
        "police", "cid", "undercover", "fbi", "mi5", "emergency",
    )},
    {"key": "foreign", "title": "Foreign and global intelligence", "families": (
        "cia", "mi6",
    )},
    {"key": "defence", "title": "Defence and special missions", "families": (
        "military", "special_ops",
    )},
    {"key": "digital", "title": "Defensive cyber research", "families": (
        "cyber",
    )},
    {"key": "executive", "title": "Presidential and imperial office research", "families": (
        "executive", "presidential", "imperial",
    )},
    {"key": "command_tree", "title": "Organisational family tree", "families": (
        "command_tree",
    )},
    {"key": "chess_roles", "title": "Chess piece-role comparison", "families": (
        "chess",
    )},
    {"key": "guardian_review", "title": "Guardian-linked safety research", "families": (
        "guardian_review",
    )},
)

# Hierarchy refers only to OAP's design. Non-agent organs are independent gates.
OAP_COMMAND_ROOT = ("Founder Final", "SMI", "Specialist research families")
CROSS_CUTTING_SYSTEM_GATES = ("Guardian", "Aegis", "Green Gate", "HRM")
REAL_WORLD_OFFICES_ARE_SUBORDINATES = False


EXTENDED_FAMILIES = tuple({
    "key": key,
    "name": name,
    "parent_world_id": world,
    "status": "family_review",
    "canonical_family": False,
} for key, name, world in EXTENDED_FAMILY_ROWS)

EXTENDED_AGENTS = tuple({
    "review_key": f"draft:{family}:{name.lower().replace(' ', '-')}",
    "name": name,
    "family_key": family,
    "role": name,
    "purpose": purpose,
    "temperament": temperament,
    "status": "passport_review",
    "canonical_agent_id": None,
    "passport_issued": False,
    "vote_eligible": False,
    "career_stars": None,
    "provider_ids": (),
    "permissions": (),
    "execution_enabled": False,
    "real_world_authority": False,
    "guardian_gate_overridden": False,
    "founder_final_required": True,
} for name, family, purpose, temperament in EXTENDED_AGENT_ROWS)


def review_status(
    registered_agents: Iterable[Mapping[str, Any]] | None = None,
    other_candidates: Iterable[Mapping[str, Any]] | None = None,
    system_names: Iterable[str] | None = None,
) -> dict[str, Any]:
    """Fail-closed, read-only candidate review. Never writes or registers agents."""
    from . import agents, specialist_agent_candidates

    canonical = tuple(agents.AGENT_REGISTRY if registered_agents is None else registered_agents)
    preceding = tuple(
        specialist_agent_candidates.PROPOSED_AGENTS
        if other_candidates is None else other_candidates
    )
    protected_systems = tuple(
        item["name"] for item in agents.ORGANISM_NON_AGENT_SYSTEMS
    ) if system_names is None else tuple(system_names)

    names = [item["name"].casefold() for item in EXTENDED_AGENTS]
    existing = {
        str(item["name"]).casefold() for item in (*canonical, *preceding)
    } | {str(name).casefold() for name in protected_systems}
    duplicates = tuple(sorted(name for name, count in Counter(names).items() if count != 1))
    clashes = tuple(item["name"] for item in EXTENDED_AGENTS if item["name"].casefold() in existing)

    parent_worlds = set(agents.LOCKED_WORLD_IDS)
    family_keys = [f["key"] for f in EXTENDED_FAMILIES]
    bad_family_keys = tuple(item["name"] for item in EXTENDED_AGENTS
                            if item["family_key"] not in family_keys)
    bad_worlds = tuple(f["key"] for f in EXTENDED_FAMILIES
                       if f["parent_world_id"] not in parent_worlds)
    incomplete = tuple(item["name"] for item in EXTENDED_AGENTS
                       if not all(item.get(k) for k in
                                  ("name", "role", "purpose", "temperament")))
    unsafe = tuple(item["name"] for item in EXTENDED_AGENTS
                   if item["execution_enabled"] or item["vote_eligible"]
                   or item["passport_issued"] or item["real_world_authority"]
                   or item["guardian_gate_overridden"]
                   or item["canonical_agent_id"] is not None
                   or item["permissions"] or item["provider_ids"]
                   or item["career_stars"] is not None)
    all_family_keys = {
        row["key"] for row in specialist_agent_candidates.SPECIALIST_FAMILIES
    } | set(family_keys)
    tree_memberships = tuple(
        family for branch in COMMAND_FAMILY_BRANCHES for family in branch["families"]
    )
    missing_tree_families = tuple(sorted(all_family_keys - set(tree_memberships)))
    unknown_tree_families = tuple(sorted(set(tree_memberships) - all_family_keys))
    duplicate_tree_families = tuple(sorted(
        key for key, count in Counter(tree_memberships).items() if count > 1
    ))
    tree_valid = not (
        missing_tree_families or unknown_tree_families or duplicate_tree_families
    ) and OAP_COMMAND_ROOT == (
        "Founder Final", "SMI", "Specialist research families"
    ) and not REAL_WORLD_OFFICES_ARE_SUBORDINATES
    ranks = UK_ARMY_RANK_REFERENCE["soldier"] + UK_ARMY_RANK_REFERENCE["officer"]
    rank_reference_valid = len(ranks) == 19 and len(set(ranks)) == 19
    valid = (
        not (duplicates or clashes or bad_family_keys or bad_worlds or incomplete or unsafe)
        and len(family_keys) == len(set(family_keys))
        and rank_reference_valid
        and tree_valid
        and len(CHESS_POSITION_ROLES) == len(set(CHESS_POSITION_ROLES)) == 6
    )
    return {
        "mode": "read_only_founder_review",
        "candidate_count": len(EXTENDED_AGENTS),
        "total_review_candidate_count": (
            len(EXTENDED_AGENTS) + len(preceding)
        ),
        "specialist_family_count": len(EXTENDED_FAMILIES),
        "draft_brief_completeness_percent": (
            round(100 * (len(EXTENDED_AGENTS) - len(incomplete)) / len(EXTENDED_AGENTS), 1)
            if EXTENDED_AGENTS else None
        ),
        "candidate_checks_passed": valid,
        "duplicate_names": duplicates,
        "name_collisions": clashes,
        "invalid_family_keys": bad_family_keys,
        "invalid_worlds": bad_worlds,
        "missing_fields": incomplete,
        "unsafe_roles": unsafe,
        "rank_reference_valid": rank_reference_valid,
        "command_family_tree": {
            "root": OAP_COMMAND_ROOT,
            "branches": COMMAND_FAMILY_BRANCHES,
            "parent_chain": "Founder Final > SMI > governed specialist families",
            "missing_family_keys": missing_tree_families,
            "unknown_family_keys": unknown_tree_families,
            "duplicate_family_keys": duplicate_tree_families,
            "valid": tree_valid,
            "cross_cutting_non_agent_gates": CROSS_CUTTING_SYSTEM_GATES,
            "film_matrix_agents_in_this_tree": False,
            "real_government_authority_claimed": False,
        },
        "chess_position_roles": CHESS_POSITION_ROLES,
        "comparative_offices": COMPARATIVE_OFFICES,
        "rank_reference": UK_ARMY_RANK_REFERENCE,
        "rank_reference_note": RANK_REFERENCE_NOTE,
        "candidates": EXTENDED_AGENTS,
        "registered_agent_count_changed": False,
        "new_passports_issued": 0,
        "founder_final_required": True,
        "guardian_is_non_agent_system": True,
        "matrix_core_unchanged": True,
        "live_readiness_percent": None,
        "overall_vpi_percent": None,
        "production_green": False,
        "truth_boundary": (
            "21 additional candidates are design briefs only. The command matrix is a family tree, NOT the film Matrix. Complete military rank "
            "reference does not prove military capability. All work is civilian, "
            "advisory and non-executing; Founder Final and Guardian are preserved."
        ),
    }
