"""OAP Digital Government: one first-party internal governance hub.

This is a Founder-private *organizational* governance dashboard grounded in
the existing canonical SMI seat register and human Judgement ledger. It is
not a sovereign nation, public authority, lawful court, government office,
election or new voting/decision/identity engine.
"""
from __future__ import annotations

from collections import Counter
from typing import Any

from . import judgement, smi_secure_seats

CHARTER_VERSION = "oap.digital-government.internal.v1"
DISPLAY_NAME = "OAP DIGITAL GOVERNMENT"
MOTTO = "EARTH IS OUR TURF"
SCOPE = "voluntary_first_party_internal_governance"
# Internal policies cannot replace a company's registered articles,
# contracts, statutory duties or the law of any jurisdiction.
OAP_LAW = (
    ("L1", "Human Authority", "Founder Final controls OAP system changes; no agent may self-authorise a release."),
    ("L2", "Dignity & Consent", "Participation is voluntary. Consent, privacy and safeguarding apply throughout."),
    ("L3", "Truth Before Green", "Record source evidence, uncertainty and test results before claiming readiness."),
    ("L4", "Independent Challenge", "Rights, appeals and compliance reviewers must be free to record dissent."),
    ("L5", "Equal Community Voice", "Public consultation needs explicit opt-in, fair rules and verified representation."),
    ("L6", "Remedy & Explanation", "People affected by important decisions need understandable reasons and human review."),
    ("L7", "Lawful Boundaries", "OAP is not a state, court, police force, elected office or source of public powers."),
)
# Unique OAP houses. "linked" is a live navigable existing first-party
# surface, NOT evidence that a new chamber or public voting service runs.
HOUSES = (
    {
        "key": "founder", "name": "Founder Chamber", "emoji": "👑",
        "purpose": "Human Authority, policies and final internal system approvals.",
        "anchor": "founder", "route": "mission_control.smi_command_dashboard_view",
        "state": "linked_existing_private_surface",
    },
    {
        "key": "cabinet", "name": "OAP Cabinet", "emoji": "🏛️",
        "purpose": "Organise ministries and specialist agent research by clear remits.",
        "anchor": "cabinet", "route": "mission_control.secure_seat_board",
        "state": "linked_existing_review_roster",
    },
    {
        "key": "commons", "name": "OAP Commons", "emoji": "🗳️",
        "purpose": "Consented private member proposals; public consultation and voting are not implemented.",
        "anchor": "commons", "route": "oap_commons.commons_home",
        "state": "linked_private_proposal_intake",
    },
    {
        "key": "boroughs", "name": "OAP Borough Councils", "emoji": "🌍",
        "purpose": "Postcode, borough, regional and international community representation.",
        "anchor": "boroughs", "route": None,
        "state": "representative_elections_not_implemented",
    },
    {
        "key": "justice", "name": "OAP Rights & Appeals", "emoji": "⚖️",
        "purpose": "Independent internal fairness reviews; no legal verdicts or penalties.",
        "anchor": "justice", "route": "mission_control.judgement_dashboard",
        "state": "linked_existing_human_review",
    },
    {
        "key": "stewardship", "name": "OAP Stewardship", "emoji": "💎",
        "purpose": "Transparent resource proposals, procurement standards and budget scrutiny.",
        "anchor": "stewardship", "route": None,
        "state": "financial_governance_not_implemented",
    },
    {
        "key": "integrity", "name": "OAP Integrity Council", "emoji": "🛡️",
        "purpose": "Guardian, Aegis, secure-seat checks, dissent and evidence boundaries.",
        "anchor": "integrity", "route": "mission_control.war_room_dashboard",
        "state": "linked_existing_war_room",
    },
)
# "Ministries" are OAP labels for research categories of *draft*
# specialist seats. No new staff positions or real public duties.
MINISTRIES = (
    ("community", "Community & Postcodes", ("gov_local", "police", "emergency")),
    ("justice", "Justice & Rights Research", (
        "court_judiciary", "court_prosecution", "court_defence",
        "court_evidence", "court_appeals", "court_jury",
    )),
    ("representation", "Representation & Civic Research", (
        "gov_executive", "gov_legislature", "gov_elections", "gov_accountability",
    )),
    ("global", "Global Relations & Culture", (
        "cia", "mi6", "imperial", "presidential", "executive",
    )),
    ("protection", "Protection & Resilience", (
        "mi5", "fbi", "undercover", "military", "special_ops",
        "guardian_review", "cyber",
    )),
    ("strategy", "Strategy & Organisational Design", (
        "command_tree", "chess",
    )),
    ("investigations", "Case & Investigation Research", ("cid",)),
)
NON_PUBLIC_GUARDS = {
    "government_or_sovereign_status": False,
    "court_judgments": False,
    "police_or_military_authority": False,
    "community_elections_enabled": False,
    "automated_personal_decisions_enabled": False,
    "member_profiling": False,
    "public_voting_enabled": False,
    "registers_agent_passports": False,
    "grants_permissions": False,
    "changes_founder_authority": False,
    "can_approve": False,
    "can_execute": False,
    "founder_final_required": True,
    "human_challenge_required": True,
}


def status() -> dict[str, Any]:
    """Read the actual SMI roster and actual Judgement readiness, fail closed."""
    roster = smi_secure_seats.board()
    if not roster["checks_passed"]:
        return {
            "name": DISPLAY_NAME,
            "charter_version": CHARTER_VERSION,
            "checks_passed": False,
            "errors": ("upstream_seat_integrity_failed",),
            "founder_final_required": True,
            "new_authority_granted": False,
            "overall_vpi_percent": None,
        }

    # Validate the full additive roster rather than constructing fictional
    # government employees. Every draft family must occur in one ministry.
    candidate_seats = tuple(
        s for branch in roster["branches"] for s in branch["candidate_seats"]
    )
    families = {str(seat["family_key"]) for seat in candidate_seats}
    assignments = [
        family for _, _, family_keys in MINISTRIES for family in family_keys
    ]
    extra = tuple(sorted(set(assignments) - families))
    missing = tuple(sorted(families - set(assignments)))
    duplicates = tuple(sorted(
        key for key, count in Counter(assignments).items() if count > 1
    ))
    law_labels = [r[0] for r in OAP_LAW]
    house_keys = [h["key"] for h in HOUSES]
    invalid_link_states = tuple(
        h["key"] for h in HOUSES
        if (h["route"] is None and h["state"].startswith("linked_"))
        or (h["route"] is not None and not h["state"].startswith("linked_"))
    )
    valid = (
        len(OAP_LAW) == len(set(law_labels)) == 7
        and len(HOUSES) == len(set(house_keys)) == 7
        and len(MINISTRIES) == 7
        and len({m[0] for m in MINISTRIES}) == 7
        and len(roster["existing_families"]) == 7
        and len(candidate_seats) == 84
        and roster["placed_existing_agents"] == 78
        and roster["total_expected"] == 162
        and not (extra or missing or duplicates or invalid_link_states)
        and all(v is False for k, v in NON_PUBLIC_GUARDS.items()
                if k not in {"founder_final_required", "human_challenge_required"})
        and NON_PUBLIC_GUARDS["founder_final_required"]
        and NON_PUBLIC_GUARDS["human_challenge_required"]
    )
    if not valid:
        return {
            "name": DISPLAY_NAME,
            "charter_version": CHARTER_VERSION,
            "checks_passed": False,
            "errors": ("digital_governance_integrity_failed",),
            "founder_final_required": True,
            "new_authority_granted": False,
            "overall_vpi_percent": None,
        }

    # Count real read-only draft placements; don't turn them into live staff.
    ministry_cards = tuple({
        "key": key,
        "name": name,
        "family_keys": keys,
        "draft_seats": sum(s["family_key"] in keys for s in candidate_seats),
        "state": "research_seats_only",
    } for key, name, keys in MINISTRIES)
    real_judgement = judgement.status()
    judgements_connected = bool(real_judgement["schema_ready"])
    return {
        "name": DISPLAY_NAME,
        "motto": MOTTO,
        "charter_version": CHARTER_VERSION,
        "scope": SCOPE,
        "checks_passed": True,
        "errors": (),
        "founder_final_required": True,
        "authority_model": "Founder Final > one SMI brain > internal advisory houses",
        "registered_existing_agents": roster["placed_existing_agents"],
        "draft_agent_seats": roster["reserved_new_candidates"],
        "mapped_seat_count": roster["total_expected"],
        "houses": HOUSES,
        "ministries": ministry_cards,
        "oap_law": tuple({
            "id": item[0], "title": item[1], "rule": item[2],
        } for item in OAP_LAW),
        "judgement": {
            "schema_connected": judgements_connected,
            "recorded_reviews": (
                real_judgement["reviews"] if judgements_connected else None
            ),
            "recorded_human_decisions": (
                real_judgement["human_decisions"] if judgements_connected else None
            ),
        },
        "safeguards": NON_PUBLIC_GUARDS,
        "new_authority_granted": False,
        "new_agent_passports_issued": 0,
        "real_community_votes_recorded": None,
        "live_constituency_representatives": None,
        "live_readiness_percent": None,
        "overall_vpi_percent": None,
        "truth_boundary": (
            "This Founder-only OAP internal government hub is a first-party"
            " organisational UI grounded in existing SMI data; it is not a"
            " government, court, charter amendment, autonomous voting system,"
            " citizenship register or public community election."
        ),
    }
