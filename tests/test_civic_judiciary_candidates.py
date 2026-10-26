"""Judicial and civic SMI research roles preserve real-world independence."""
from __future__ import annotations

from mission_control import agents
from mission_control import civic_judiciary_candidates as spec


def test_twenty_one_court_and_twenty_one_civic_agents_in_eleven_families():
    report = spec.review_status()
    assert report["candidate_checks_passed"] is True, report
    assert report["judicial_candidate_count"] == 21
    assert report["civic_candidate_count"] == 21
    assert report["candidate_count"] == 42
    assert report["family_count"] == 11
    assert report["draft_brief_completeness_percent"] == 100.0
    assert len({a["review_key"] for a in spec.COURT_AND_GOVERNMENT_AGENTS}) == 42
    assert len({a["name"] for a in spec.COURT_AND_GOVERNMENT_AGENTS}) == 42
    assert len(agents.AGENT_REGISTRY) == agents.LOCKED_AGENT_COUNT == 78


def test_courts_legislatures_and_local_actors_not_subordinates_of_president():
    report = spec.review_status()
    assert not report["independence_violations"]
    assert set(report["independent_powers"]) == {
        "executive", "legislature", "judiciary",
        "regional_local", "elections", "accountability",
    }
    for country, relations in report["country_reference_relations"].items():
        assert country in {"US", "UK", "Ghana"}
        assert all(relation not in spec.BANNED_REAL_WORLD_HIERARCHY
                   for relation in relations)
    assert report["registry_mutated"] is False


def test_internal_smi_judges_not_given_real_court_or_political_powers():
    for a in spec.COURT_AND_GOVERNMENT_AGENTS:
        assert a["canonical_agent_id"] is None
        assert a["passport_issued"] is False
        assert a["vote_eligible"] is False
        assert a["career_stars"] is None
        assert a["execution_enabled"] is False
        assert a["real_world_authority"] is False
        assert a["election_persuasion_enabled"] is False
        assert a["court_order_enabled"] is False
        assert a["personal_surveillance_enabled"] is False
        assert not a["permissions"]
        assert not a["provider_ids"]
        assert a["founder_final_required"] is True


def test_court_and_civic_family_tree_memberships_unique():
    branches = spec.GOVERNMENT_FAMILY_BRANCHES
    members = [family for b in branches for family in b["families"]]
    assert len(branches) == 4
    assert len(members) == len(set(members)) == 11
    assert set(members) == {
        f["key"] for f in spec.COURT_AND_GOVERNMENT_FAMILIES
    }


def test_proposals_fail_closed_when_name_collides():
    bad = spec.review_status(preceding_candidates=(
        {"name": "Chief Justice Role Researcher"},
    ))
    assert bad["candidate_checks_passed"] is False
    assert "Chief Justice Role Researcher" in bad["name_collisions"]


def test_civic_risk_never_translates_to_deployed_readiness():
    report = spec.review_status()
    assert report["new_passports_issued"] == 0
    assert report["can_execute"] is False
    assert report["can_render_court_verdicts"] is False
    assert report["can_influence_elections"] is False
    assert report["live_readiness_percent"] is None
    assert report["overall_vpi_percent"] is None
