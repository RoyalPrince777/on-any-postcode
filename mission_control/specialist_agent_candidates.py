"""Review-only SMI specialist agent candidates; never registered or executable.

These original fictional identities borrow organisational *research themes*, not
government affiliation, policing powers, covert access or emergency dispatch.
The 78-agent canonical registry and its passports remain unchanged.
"""
from __future__ import annotations

from collections import Counter
from typing import Any, Iterable, Mapping

# Family rows: review key, specialist family name, existing SMI parent world.
FAMILY_ROWS = [["police","Police Intelligence","civic"],["cid","CID Detective Intelligence","civic"],["undercover","Undercover Safeguards Intelligence","civic"],["fbi","Federal Investigation Research","civic"],["cia","Foreign Intelligence Research","civilisation"],["mi5","Domestic Security Research","civic"],["mi6","Overseas Intelligence Research","civilisation"],["military","Defence Intelligence Research","civilisation"],["special_ops","Special Operations Planning","movement"],["emergency","Emergency Referral Intelligence","life"],["cyber","Cyber Defence Intelligence","matrix"],["executive","Executive Intelligence Briefing","civilisation"]]
# Candidate rows: name, family key, fictional role, bounded purpose, temperament.
AGENT_ROWS = [["Rowan","police","Police Constable","Public incident intake and evidence-safe reporting","steady"],["Vale","police","Police Sergeant","First-line team supervision and triage","calm"],["Hart","police","Police Inspector","Service-risk review and escalation governance","measured"],["Quinn","cid","Detective Constable","Documented case research and timeline reconstruction","curious"],["Mercer","cid","Detective Inspector","Case coordination and evidence contradictions","methodical"],["Cross","cid","Detective Chief Inspector","Complex-case review and proportionate recommendations","discerning"],["Nyx","undercover","Confidentiality Specialist","Protection of confidential reports and source privacy","reserved"],["Slate","undercover","Covert Safeguards Reviewer","Legality, necessity and prohibition of impersonation","principled"],["Meridian","fbi","Federal Research Analyst","Cross-jurisdiction public-source investigations","persistent"],["Ledger","fbi","Financial Case Researcher","Fraud indicators and transaction evidence analysis","precise"],["Horizon","cia","Foreign Threat Researcher","Geopolitical threat assessment from permitted sources","far-sighted"],["Atlas","cia","Source Reliability Analyst","Foreign-source corroboration and confidence grading","sceptical"],["Bastion","mi5","Domestic Protection Researcher","Domestic security risk and protective advice","vigilant"],["Threshold","mi5","Insider Risk Analyst","Defensive insider-risk patterns and proportional safeguards","balanced"],["Farpoint","mi6","Overseas Research Analyst","International risk analysis from lawful sources","observant"],["Crosswind","mi6","Global Crisis Researcher","Foreign crisis context and cross-source comparison","adaptable"],["Vector","military","Defence Risk Analyst","Defensive threat modelling and infrastructure resilience","disciplined"],["Waypoint","special_ops","Mission Planning Analyst","Non-operational response coordination and exit criteria","focused"],["Beacon","emergency","Emergency Referral Analyst","Emergency triage guidance and official-service referral","compassionate"],["Cipher","cyber","Cyber Defence Analyst","Authorised security triage and digital-evidence integrity","technical"],["Northstar","executive","Executive Briefing Analyst","Evidence-grounded Founder briefings and dissent summary","impartial"]]

SPECIALIST_FAMILIES = tuple(
    {"key": key, "name": name, "parent_world_id": world,
     "status": "family_review", "canonical_family": False}
    for key, name, world in FAMILY_ROWS
)
PROPOSED_AGENTS = tuple(
    {
        "review_key": f"draft:{family}:{name.lower()}",
        "name": name,
        "family_key": family,
        "fictional_role": role,
        "purpose": purpose,
        "temperament": temperament,
        "review_status": "passport_review",
        "canonical_agent_id": None,
        "passport_issued": False,
        "vote_eligible": False,
        "career_stars": None,
        "performance_rating": "UNRATED",
        "provider_ids": (),
        "permissions": (),
        "execution_enabled": False,
        "real_world_authority": False,
        "founder_final_required": True,
    }
    for name, family, role, purpose, temperament in AGENT_ROWS
)

def review_status(
    registered_agents: Iterable[Mapping[str, Any]] | None = None,
    non_agent_system_names: Iterable[str] | None = None,
) -> dict[str, Any]:
    """Read-only War Room candidate audit; no votes, passports or writes."""
    if registered_agents is None or non_agent_system_names is None:
        from . import agents
        if registered_agents is None:
            registered_agents = agents.AGENT_REGISTRY
        if non_agent_system_names is None:
            non_agent_system_names = (
                system["name"] for system in agents.ORGANISM_NON_AGENT_SYSTEMS
            )
        valid_worlds = set(agents.LOCKED_WORLD_IDS)
    else:
        valid_worlds = {"earth", "language", "life", "movement", "civic",
                        "civilisation", "matrix"}

    families = {item["key"] for item in SPECIALIST_FAMILIES}
    all_names = [item["name"].casefold() for item in PROPOSED_AGENTS]
    registry_names = {str(item["name"]).casefold() for item in registered_agents}
    system_names = {str(name).casefold() for name in non_agent_system_names}
    duplicates = tuple(sorted(
        name for name, count in Counter(all_names).items() if count > 1
    ))
    clashes = tuple(sorted(
        item["name"] for item in PROPOSED_AGENTS
        if item["name"].casefold() in registry_names | system_names
    ))
    unknown_families = tuple(sorted(
        item["name"] for item in PROPOSED_AGENTS if item["family_key"] not in families
    ))
    bad_worlds = tuple(sorted(
        item["key"] for item in SPECIALIST_FAMILIES
        if item["parent_world_id"] not in valid_worlds
    ))
    incomplete = tuple(sorted(
        item["name"] for item in PROPOSED_AGENTS
        if not all(item[field] for field in ("name", "fictional_role", "purpose", "temperament"))
    ))
    unsafe = tuple(sorted(
        item["name"] for item in PROPOSED_AGENTS
        if item["execution_enabled"] or item["vote_eligible"]
        or item["passport_issued"] or item["real_world_authority"]
        or item["canonical_agent_id"] is not None
        or item["permissions"] or item["provider_ids"] or item["career_stars"] is not None
    ))
    families_valid = len(families) == len(SPECIALIST_FAMILIES)
    checks_passed = not (
        duplicates or clashes or unknown_families or bad_worlds or incomplete or unsafe
    ) and families_valid
    defined_briefs = len(PROPOSED_AGENTS) - len(incomplete)
    total_briefs = len(PROPOSED_AGENTS)
    return {
        "mode": "read_only_founder_review",
        "family_count": len(SPECIALIST_FAMILIES),
        "candidate_count": total_briefs,
        "draft_brief_completeness_percent": round(
            100 * defined_briefs / total_briefs, 1
        ) if total_briefs else None,
        "families": SPECIALIST_FAMILIES,
        "candidates": PROPOSED_AGENTS,
        "candidate_checks_passed": checks_passed,
        "collisions": clashes,
        "duplicates": duplicates,
        "unknown_families": unknown_families,
        "invalid_parent_worlds": bad_worlds,
        "incomplete_briefs": incomplete,
        "unsafe_candidates": unsafe,
        "registered_agent_count_changed": False,
        "runtime_readiness_percent": None,
        "overall_vpi_percent": None,
        "promotion_authorised": False,
        "founder_final_required": True,
        "truth_boundary": (
            "Candidate briefs and static review are not canonical passports, "
            "real independent votes, 24/7 staffing, production capability, or green gates."
        ),
    }
