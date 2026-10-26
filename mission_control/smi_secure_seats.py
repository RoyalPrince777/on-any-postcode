"""Founder-only, read-only SMI War Room secure seat register.

A *seat* is a deterministic display placement, never a credential, access right,
governance vote, passport, permanent appointment or running autonomous worker.
The canonical 78 agents are referenced by their existing passports only.
The 84 draft specialists have locked REVIEW seats without active identities.
System protection gates, government offices, military ranks and chess pieces
are reference stations -- never agent seats or authority grants.
"""
from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from typing import Any

from . import (
    agents,
    civic_judiciary_candidates,
    specialist_agent_candidates,
    specialist_command_candidates,
)

EXPECTED_CANONICAL = agents.LOCKED_AGENT_COUNT
EXPECTED_REVIEW = 84
EXPECTED_TOTAL = EXPECTED_CANONICAL + EXPECTED_REVIEW
SENTINEL = ("Founder Final", "SMI", "Specialist research families")
PROTECTED_GATES = ("Guardian", "Aegis", "Green Gate", "HRM")
GOVERNANCE_POLICY = {
    "mode": "founder_only_read_only",
    "controls_enabled": False,
    "can_execute": False,
    "can_approve": False,
    "can_vote": False,
    "creates_passports": False,
    "issues_credentials": False,
    "changes_registry": False,
    "independent_review_required": True,
    "founder_final_required": True,
    "human_authority_final": True,
}


def _seat_rows(
    canonical: Iterable[Mapping[str, Any]],
    proposed: Iterable[Mapping[str, Any]],
) -> tuple[dict[str, Any], ...]:
    """Preserve original IDs, use visibly non-credentialled draft review keys."""
    canonical_seats = tuple({
        "seat_key": f"canonical:{agent['agent_id']}",
        "name": str(agent["name"]),
        "identity_ref": str(agent["agent_id"]),
        "family_key": str(agent["family_id"]),
        "kind": "registered_agent_reference",
        "status": "canonical_registry_only",
        "permissions_granted": False,
        "passport_issued_by_seat": False,
        "vote_from_seat_allowed": False,
        "execution_from_seat_allowed": False,
    } for agent in canonical)
    candidate_seats = tuple({
        "seat_key": f"review:{agent['review_key']}",
        "name": str(agent["name"]),
        "identity_ref": None,
        "family_key": str(agent["family_key"]),
        "kind": "specialist_candidate",
        "status": "reserved_review_only",
        "permissions_granted": False,
        "passport_issued_by_seat": False,
        "vote_from_seat_allowed": False,
        "execution_from_seat_allowed": False,
    } for agent in proposed)
    return canonical_seats + candidate_seats


def board(
    canonical_agents: Iterable[Mapping[str, Any]] | None = None,
    proposed_agents: Iterable[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Return ALL seats only when the complete no-privilege audit passes."""
    canonical = tuple(agents.AGENT_REGISTRY if canonical_agents is None else canonical_agents)
    new_agents = tuple(
        (*specialist_agent_candidates.PROPOSED_AGENTS,
         *specialist_command_candidates.EXTENDED_AGENTS,
         *civic_judiciary_candidates.COURT_AND_GOVERNMENT_AGENTS)
        if proposed_agents is None else proposed_agents
    )
    seats = _seat_rows(canonical, new_agents)
    keys = [str(s["seat_key"]) for s in seats]
    names = [str(s["name"]).casefold() for s in seats]
    duplicates = sorted(
        {name for name, count in Counter(names).items() if count > 1}
    )
    key_collisions = sorted(
        {key for key, count in Counter(keys).items() if count > 1}
    )
    protected = {str(s["name"]).casefold() for s in agents.ORGANISM_NON_AGENT_SYSTEMS}
    protected |= {x.casefold() for x in PROTECTED_GATES}
    protected_collisions = sorted(
        s["name"] for s in seats if s["name"].casefold() in protected
    )

    family_tree = (
        *specialist_command_candidates.COMMAND_FAMILY_BRANCHES,
        *civic_judiciary_candidates.GOVERNMENT_FAMILY_BRANCHES,
    )
    memberships = [family for area in family_tree for family in area["families"]]
    proposed_families = {
        str(f["key"]) for f in
        (*specialist_agent_candidates.SPECIALIST_FAMILIES,
         *specialist_command_candidates.EXTENDED_FAMILIES,
         *civic_judiciary_candidates.COURT_AND_GOVERNMENT_FAMILIES)
    }
    expected_families = set(memberships)
    canonical_family_ids = set(agents.LOCKED_FAMILY_IDS)
    orphaned = sorted(proposed_families - expected_families)
    unspecified = sorted(expected_families - proposed_families)
    repeated_families = sorted(
        k for k, v in Counter(memberships).items() if v != 1
    )
    unknown_registered_families = sorted(
        s["family_key"] for s in seats
        if s["kind"] == "registered_agent_reference"
        and s["family_key"] not in canonical_family_ids
    )
    unknown_draft_families = sorted(
        s["family_key"] for s in seats
        if s["kind"] == "specialist_candidate"
        and s["family_key"] not in proposed_families
    )
    invalid_source = sorted(
        s["seat_key"] for s in seats
        if (s["kind"] == "specialist_candidate"
            and (s["identity_ref"] is not None
                 or not s["seat_key"].startswith("review:draft:")))
        or (s["kind"] == "registered_agent_reference"
            and (not s["identity_ref"]
                 or not s["seat_key"].startswith("canonical:")))
        or (s["permissions_granted"] or s["passport_issued_by_seat"]
            or s["vote_from_seat_allowed"] or s["execution_from_seat_allowed"])
    )
    invalid_proposals = sorted(
        str(a.get("name")) for a in new_agents
        if (a.get("canonical_agent_id") is not None
            or a.get("passport_issued") is not False
            or a.get("vote_eligible") is not False
            or a.get("execution_enabled") is not False
            or a.get("real_world_authority") is not False
            or a.get("founder_final_required") is not True
            or bool(a.get("permissions")) or bool(a.get("provider_ids"))
            or a.get("career_stars") is not None
            or a.get("election_persuasion_enabled", False)
            or a.get("court_order_enabled", False)
            or a.get("personal_surveillance_enabled", False))
    )
    invalid_canonical_ids = sorted(
        str(a.get("name", "")) for a in canonical if not a.get("agent_id")
    )
    canonical_key_unique = len({
        str(a.get("agent_id")) for a in canonical
    }) == len(canonical)
    # No modified or fabricated population count qualifies as a secured roster.
    passed = (
        len(canonical) == EXPECTED_CANONICAL
        and len(new_agents) == EXPECTED_REVIEW
        and len(seats) == EXPECTED_TOTAL
        and canonical_key_unique
        and not (
            duplicates or key_collisions or protected_collisions
            or orphaned or unspecified or repeated_families
            or unknown_registered_families or unknown_draft_families
            or invalid_source or invalid_proposals or invalid_canonical_ids
        )
        and specialist_agent_candidates.review_status()["candidate_checks_passed"]
        and specialist_command_candidates.review_status()["candidate_checks_passed"]
        and civic_judiciary_candidates.review_status()["candidate_checks_passed"]
        and specialist_command_candidates.OAP_COMMAND_ROOT == SENTINEL
        and not specialist_command_candidates.REAL_WORLD_OFFICES_ARE_SUBORDINATES
    )

    errors = tuple(k for k, v in (
        ("seat_count_mismatch", len(seats) != EXPECTED_TOTAL),
        ("registry_population_invalid", len(canonical) != EXPECTED_CANONICAL),
        ("candidate_population_invalid", len(new_agents) != EXPECTED_REVIEW),
        ("duplicate_seat_keys", bool(key_collisions) or not canonical_key_unique),
        ("duplicate_seat_names", bool(duplicates)),
        ("system_agent_collision", bool(protected_collisions)),
        ("missing_family_assignment", bool(orphaned or unspecified or repeated_families)),
        ("invalid_family_assignment", bool(unknown_registered_families or unknown_draft_families)),
        ("privileged_or_invalid_seat", bool(invalid_source or invalid_proposals)),
        ("canonical_identity_missing", bool(invalid_canonical_ids)),
        ("upstream_candidate_review_failed", not (
            specialist_agent_candidates.review_status()["candidate_checks_passed"]
            and specialist_command_candidates.review_status()["candidate_checks_passed"]
            and civic_judiciary_candidates.review_status()["candidate_checks_passed"]
        )),
    ) if v)

    branches = tuple({
        "key": item["key"], "title": item["title"],
        "family_keys": item["families"],
        "candidate_seats": tuple(
            seat for seat in seats if seat["kind"] == "specialist_candidate"
            and seat["family_key"] in item["families"]
        ),
    } for item in family_tree) if passed else ()

    original_families = tuple({
        "family_key": family["id"],
        "name": family["name"],
        "seats": tuple(
            seat for seat in seats
            if seat["kind"] == "registered_agent_reference"
            and seat["family_key"] == family["id"]
        ),
    } for family in agents.INTELLIGENCE_FAMILIES) if passed else ()

    # These are NON-AGENT reference positions, not extra passports.
    reference_positions = {
        "chess_pieces": specialist_command_candidates.CHESS_POSITION_ROLES,
        "government_offices": (
            "President (comparative office)", "Emperor (comparative office)"
        ),
        "constitutional_relations": civic_judiciary_candidates.COUNTRY_REFERENCE_RELATIONS,
        "civic_independent_powers": civic_judiciary_candidates.INDEPENDENT_BRACKET,
        "court_agents_are_not_real_judges": True,
        "political_agents_are_nonpartisan_research_only": True,
        "military_ranks": specialist_command_candidates.UK_ARMY_RANK_REFERENCE,
        "protected_governance_stations": PROTECTED_GATES,
    }

    return {
        "name": "SMI Secure Seat Register",
        "mode": "founder_only_read_only",
        "seat_scope": "static_display_placement_not_runtime_or_authentication",
        "checks_passed": passed,
        "errors": errors,
        "expected_canonical_seats": EXPECTED_CANONICAL,
        "expected_review_seats": EXPECTED_REVIEW,
        "total_expected": EXPECTED_TOTAL,
        "placed_existing_agents": len(canonical) if passed else 0,
        "reserved_new_candidates": len(new_agents) if passed else 0,
        "seat_placement_coverage_percent": 100.0 if passed else None,
        "branches": branches,
        "existing_families": original_families,
        "reference_positions": reference_positions,
        "safeguards": GOVERNANCE_POLICY,
        "new_agents_activated": 0,
        "new_court_research_seats": 21 if passed else 0,
        "new_civic_research_seats": 21 if passed else 0,
        "new_agent_passports_issued": 0,
        "independent_votes_recorded": False,
        "career_stars_awarded": False,
        "overall_vpi_percent": None,
        "live_readiness_percent": None,
        "truth_boundary": (
            "A secure seat is a Founder-private review placement only, not an"
            " issued credential, functioning AI agent, armed service, government"
            " position, legal judgment, electoral campaigning, independent vote,"
            " operating protection service, or release."
        ),
    }
