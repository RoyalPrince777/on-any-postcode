"""Founder-review-only legal courts and civic constitutional agent candidates.

These are 42 standalone role-named research candidates, NOT judges, lawyers,
public officials, elected agents or substitutes for independent institutions.
Prior 78 registered SMI identities and 42 original specialist drafts stay intact.
No government affiliation, coercive power, electoral advocacy or political
profiling is granted. Real branches and local tiers remain independent as law
requires. Internal SMI seven-judge quality review is NOT a civil/criminal court.
"""
from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from typing import Any

FAMILY_ROWS = [["court_judiciary","Judicial Office and Court Administration","civic"],["court_prosecution","Prosecution Procedure Research","civic"],["court_defence","Independent Defence and Legal Rights Research","civic"],["court_evidence","Court Evidence and Witness Safeguarding","civic"],["court_appeals","Judicial Appeals and Review","civic"],["court_jury","Jury and Public Justice Process","civic"],["gov_executive","Executive Government Office Research","civilisation"],["gov_legislature","Parliament and Legislative Intelligence","civic"],["gov_local","Regional and Local Government Research","civic"],["gov_elections","Nonpartisan Electoral Administration Research","civic"],["gov_accountability","Independent Public Accountability Research","civic"]]
# (functional name, family key, lawful advisory purpose, perspective)
AGENT_ROWS = [["Chief Justice Role Researcher","court_judiciary","Compare documented Chief Justice functions and judicial independence","impartial"],["Deputy Judicial Administration Researcher","court_judiciary","Research judicial leadership succession and court administration","systematic"],["Court Administrator Researcher","court_judiciary","Map court services and administrative process without adjudication","orderly"],["Court Clerk Records Researcher","court_judiciary","Research official case-record handling and court calendars","precise"],["Court Marshal Procedure Researcher","court_judiciary","Research courtroom order and court security safeguards; no policing","restrained"],["Public Prosecutor Procedure Analyst","court_prosecution","Describe prosecutorial processes and public evidence thresholds","objective"],["Prosecutorial Disclosure Researcher","court_prosecution","Study lawful prosecution disclosure and fair trial duties","scrupulous"],["Defence Counsel Rights Researcher","court_defence","Explain procedural defence rights from published legal sources","protective"],["Independent Legal Aid Researcher","court_defence","Study legal advice access and representation pathways","empathetic"],["Court Evidence Admissibility Analyst","court_evidence","Research reliability, provenance and admissibility standards","careful"],["Digital Court Forensics Researcher","court_evidence","Review digital-evidence integrity using permitted source material","methodical"],["Witness Safeguarding Researcher","court_evidence","Explain witness support and privacy safeguards","compassionate"],["Case Timeline and Contradiction Analyst","court_evidence","Compare public case timelines and source contradictions","sceptical"],["Appeal Procedure Researcher","court_appeals","Map appellate routes and requirements by jurisdiction","patient"],["Judicial Review Researcher","court_appeals","Explain court review of public decisions without giving rulings","balanced"],["Appellate Counsel Process Analyst","court_appeals","Research published appeals practice and rights","analytical"],["Independent Judicial Impartiality Auditor","court_appeals","Evaluate proposed OAP research summaries for procedural neutrality","independent"],["Jury Selection Process Researcher","court_jury","Compare lawful jury selection and eligibility frameworks","fair-minded"],["Jury Foreperson Procedure Researcher","court_jury","Explain jury foreperson responsibilities and group deliberation rules","composed"],["Court Guardian and HRM Liaison Researcher","court_jury","Check research consent, retention and independent governance boundaries","principled"],["Court Human Authority Liaison Researcher","court_jury","Verify that agent advice never becomes a judicial order or punishment","firm"],["Presidential Office Structure Analyst","gov_executive","Compare President, Cabinet and adviser roles by constitution","neutral"],["Vice Presidency Succession Analyst","gov_executive","Research vice-presidential duties and succession safeguards","accurate"],["Prime Minister Cabinet Analyst","gov_executive","Research UK parliamentary executive and Cabinet accountability","even-handed"],["Ministerial Department Analyst","gov_executive","Study policy implementation through ministries and departments","practical"],["Civil Service Administration Analyst","gov_executive","Distinguish elected ministers from permanent public servants","methodical"],["Government Agency Governance Analyst","gov_executive","Map statutory departments, commissions and delegated powers","careful"],["Parliament and Congress Role Analyst","gov_legislature","Research how national legislatures make law and scrutinise government","civic-minded"],["Senate and Upper Chamber Analyst","gov_legislature","Compare upper chambers, representation and delegated duties","precise"],["Legislative Committee Scrutiny Analyst","gov_legislature","Study committee hearings, evidence and oversight records","thorough"],["Independent Opposition Scrutiny Analyst","gov_legislature","Present public opposition and minority oversight functions neutrally","impartial"],["Governor and Regional Government Analyst","gov_local","Compare state, regional and devolved executive authority","grounded"],["Executive Mayor Governance Analyst","gov_local","Explain elected mayor authority and municipal responsibilities","practical"],["Civic Mayor Ceremonial Role Analyst","gov_local","Distinguish civic ceremonial mayors from elected executives","exact"],["Local Councillor Representation Analyst","gov_local","Study ward representation, public meetings and declared interests","accessible"],["Council Cabinet and Committee Analyst","gov_local","Describe council delegation, scrutiny and public minutes","organised"],["Municipal Services and District Assembly Analyst","gov_local","Compare municipal services and Ghana district assembly structures","locally-aware"],["Election Administration Researcher","gov_elections","Provide neutral election process and eligibility information","nonpartisan"],["Independent Electoral Integrity Researcher","gov_elections","Research published voting safeguards without influencing voters","nonpartisan"],["Ombudsman and Public Complaints Analyst","gov_accountability","Explain public complaints, remedies and ombudsman routes","respectful"],["Public Audit and Anti-Corruption Researcher","gov_accountability","Research lawful audit transparency and anti-corruption institutions","evidence-led"],["Traditional Authority and Devolution Researcher","gov_accountability","Distinguish Ghanaian traditional authorities and devolved public offices","culturally-aware"]]
JUDICIARY_FAMILY_KEYS = (
    "court_judiciary", "court_prosecution", "court_defence",
    "court_evidence", "court_appeals", "court_jury",
)
CIVIC_FAMILY_KEYS = (
    "gov_executive", "gov_legislature", "gov_local",
    "gov_elections", "gov_accountability",
)
# Research-only examples; not a universal single line from president to mayor.
# "separate_from" and "scrutinises" expressly prohibit subordination claims.
COUNTRY_REFERENCE_RELATIONS = {
    "US": (
        ("President", "heads", "Federal executive branch"),
        ("Vice President", "supports", "President"),
        ("Cabinet", "advises", "President"),
        ("Congress", "legislates_separately_from", "President"),
        ("Federal courts", "adjudicate_independently_from", "President"),
        ("State governments", "have_constitutional_powers_distinct_from", "Federal government"),
        ("Mayors and local councils", "govern_under", "State and local law"),
    ),
    "UK": (
        ("Prime Minister", "heads", "UK Government"),
        ("Cabinet", "supports", "Prime Minister"),
        ("Parliament", "scrutinises", "UK Government"),
        ("Courts", "adjudicate_independently_from", "UK Government"),
        ("Council executives and councillors", "govern_under", "Local government law"),
        ("Ceremonial mayors", "differ_from", "Executive mayors"),
    ),
    "Ghana": (
        ("President", "heads", "National executive"),
        ("Cabinet and ministers", "support", "President"),
        ("Parliament", "legislates_separately_from", "President"),
        ("Judiciary", "adjudicates_independently_from", "President"),
        ("District assemblies", "operate_under", "Local governance constitutional law"),
        ("Traditional authorities", "have_distinct_legal_roles_from", "National executive"),
    ),
}
INDEPENDENT_BRACKET = (
    "executive", "legislature", "judiciary", "regional_local",
    "elections", "accountability",
)
BANNED_REAL_WORLD_HIERARCHY = (
    ("Congress", "reports_to", "President"),
    ("Federal courts", "reports_to", "President"),
    ("Parliament", "reports_to", "President"),
    ("Judiciary", "reports_to", "President"),
    ("Courts", "reports_to", "Prime Minister"),
)
PUBLIC_INFORMATION_ONLY = True
POLITICAL_NEUTRALITY_REQUIRED = True

COURT_AND_GOVERNMENT_FAMILIES = tuple({
    "key": key, "name": title, "parent_world_id": world,
    "status": "family_review", "canonical_family": False,
} for key, title, world in FAMILY_ROWS)

COURT_AND_GOVERNMENT_AGENTS = tuple({
    "review_key": f"draft:{family}:{name.lower().replace(' ', '-')}",
    "name": name, "family_key": family, "role": name,
    "purpose": purpose, "temperament": temperament,
    "status": "passport_review",
    "canonical_agent_id": None, "passport_issued": False,
    "vote_eligible": False, "career_stars": None,
    "permissions": (), "provider_ids": (),
    "execution_enabled": False, "real_world_authority": False,
    "election_persuasion_enabled": False, "court_order_enabled": False,
    "personal_surveillance_enabled": False,
    "founder_final_required": True,
} for name, family, purpose, temperament in AGENT_ROWS)

# Additive family-tree branches; never rewrite the original eight branches.
GOVERNMENT_FAMILY_BRANCHES = (
    {"key": "court_process", "title": "Independent courts and judicial research",
     "families": ("court_judiciary", "court_evidence", "court_appeals", "court_jury")},
    {"key": "legal_rights", "title": "Prosecution and independent legal defence",
     "families": ("court_prosecution", "court_defence")},
    {"key": "constitutional", "title": "Executive and legislative comparison",
     "families": ("gov_executive", "gov_legislature")},
    {"key": "local_accountability", "title": "Governors, mayors, councils, elections and oversight",
     "families": ("gov_local", "gov_elections", "gov_accountability")},
)


def review_status(
    registered_agents: Iterable[Mapping[str, Any]] | None = None,
    preceding_candidates: Iterable[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Fail-closed, read-only validation of independent court/civic candidates."""
    from . import agents, specialist_agent_candidates, specialist_command_candidates

    canonical = tuple(agents.AGENT_REGISTRY if registered_agents is None else registered_agents)
    preceding = tuple(
        (*specialist_agent_candidates.PROPOSED_AGENTS,
         *specialist_command_candidates.EXTENDED_AGENTS)
        if preceding_candidates is None else preceding_candidates
    )
    known_names = {
        str(item["name"]).casefold() for item in (*canonical, *preceding)
    } | {
        str(item["name"]).casefold() for item in agents.ORGANISM_NON_AGENT_SYSTEMS
    }
    names = [item["name"].casefold() for item in COURT_AND_GOVERNMENT_AGENTS]
    duplicate_names = tuple(sorted(
        name for name, amount in Counter(names).items() if amount != 1
    ))
    collisions = tuple(
        item["name"] for item in COURT_AND_GOVERNMENT_AGENTS
        if item["name"].casefold() in known_names
    )
    keys = [item["key"] for item in COURT_AND_GOVERNMENT_FAMILIES]
    invalid_worlds = tuple(
        item["key"] for item in COURT_AND_GOVERNMENT_FAMILIES
        if item["parent_world_id"] not in agents.LOCKED_WORLD_IDS
    )
    invalid_families = tuple(
        item["name"] for item in COURT_AND_GOVERNMENT_AGENTS
        if item["family_key"] not in keys
    )
    missing_briefs = tuple(
        item["name"] for item in COURT_AND_GOVERNMENT_AGENTS
        if not all(item.get(key) for key in ("name", "role", "purpose", "temperament"))
    )
    unsafe = tuple(
        item["name"] for item in COURT_AND_GOVERNMENT_AGENTS
        if item["execution_enabled"] or item["vote_eligible"]
        or item["real_world_authority"] or item["passport_issued"]
        or item["election_persuasion_enabled"] or item["court_order_enabled"]
        or item["personal_surveillance_enabled"]
        or item["canonical_agent_id"] is not None
        or item["career_stars"] is not None
        or item["permissions"] or item["provider_ids"]
        or item["founder_final_required"] is not True
    )
    relations = tuple(
        relation for country in COUNTRY_REFERENCE_RELATIONS.values()
        for relation in country
    )
    violations = tuple(relation for relation in relations if relation in BANNED_REAL_WORLD_HIERARCHY)
    branches = [
        key for area in GOVERNMENT_FAMILY_BRANCHES for key in area["families"]
    ]
    tree_invalid = (
        set(branches) != set(keys) or len(branches) != len(set(branches))
        or set(JUDICIARY_FAMILY_KEYS) | set(CIVIC_FAMILY_KEYS) != set(keys)
        or len(agents.LOCKED_WORLD_IDS) != 7
        or bool(violations)
        or not PUBLIC_INFORMATION_ONLY
        or not POLITICAL_NEUTRALITY_REQUIRED
    )
    passed = (
        len(COURT_AND_GOVERNMENT_AGENTS) == 42
        and len(JUDICIARY_FAMILY_KEYS) == 6
        and len(CIVIC_FAMILY_KEYS) == 5
        and len(keys) == len(set(keys)) == 11
        and not (
            duplicate_names or collisions or invalid_worlds or invalid_families
            or missing_briefs or unsafe or tree_invalid
        )
    )
    return {
        "mode": "read_only_founder_review",
        "candidate_checks_passed": passed,
        "judicial_candidate_count": sum(
            1 for a in COURT_AND_GOVERNMENT_AGENTS
            if a["family_key"] in JUDICIARY_FAMILY_KEYS
        ),
        "civic_candidate_count": sum(
            1 for a in COURT_AND_GOVERNMENT_AGENTS
            if a["family_key"] in CIVIC_FAMILY_KEYS
        ),
        "candidate_count": len(COURT_AND_GOVERNMENT_AGENTS),
        "family_count": len(COURT_AND_GOVERNMENT_FAMILIES),
        "draft_brief_completeness_percent": (
            round(100 * (len(COURT_AND_GOVERNMENT_AGENTS) - len(missing_briefs))
                  / len(COURT_AND_GOVERNMENT_AGENTS), 1)
            if COURT_AND_GOVERNMENT_AGENTS else None
        ),
        "missing_briefs": missing_briefs,
        "duplicate_names": duplicate_names,
        "name_collisions": collisions,
        "invalid_families": invalid_families,
        "invalid_worlds": invalid_worlds,
        "unsafe": unsafe,
        "independence_violations": violations,
        "country_reference_relations": COUNTRY_REFERENCE_RELATIONS,
        "independent_powers": INDEPENDENT_BRACKET,
        "families": COURT_AND_GOVERNMENT_FAMILIES,
        "candidates": COURT_AND_GOVERNMENT_AGENTS,
        "registry_mutated": False,
        "new_passports_issued": 0,
        "can_execute": False,
        "can_render_court_verdicts": False,
        "can_influence_elections": False,
        "founder_final_required": True,
        "live_readiness_percent": None,
        "overall_vpi_percent": None,
        "truth_boundary": (
            "All court and civic seats are proposed research roles, not real"
            " judicial office-holders, political agents, election advocates,"
            " officials, legal practitioners or sovereign decision-makers."
        ),
    }
