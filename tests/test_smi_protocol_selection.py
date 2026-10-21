"""Negative boundaries for SMI advisory protocol recommendations."""
from oap.smi.protocol_selection import PROTOCOL_TEAMS, recommend_protocol_team


def test_all_28_protocols_have_unique_leads_and_no_duplicate_members():
    assert len(PROTOCOL_TEAMS) == 28
    for lead, specialists in PROTOCOL_TEAMS.values():
        assert lead
        assert lead not in specialists
        assert len(specialists) == len(set(specialists))


def test_known_team_is_advisory_and_unverified():
    result = recommend_protocol_team("stealth")
    assert result.lead == "Bagheera"
    assert result.status == "PROPOSED_UNVERIFIED"
    assert result.advisory_only
    assert not result.grants_permissions
    assert result.human_authority_final


def test_unknown_protocol_fails_closed():
    result = recommend_protocol_team("unregistered-protocol")
    assert result.lead is None
    assert result.specialists == ()
    assert result.status == "UNRECOGNISED"
    assert not result.grants_permissions


def test_non_string_input_fails_closed():
    assert recommend_protocol_team(None).status == "UNRECOGNISED"
    assert recommend_protocol_team({}).lead is None


def test_auto_mission_roles_are_advisory_and_unverified():
    from oap.smi.protocol_selection import recommend_mission_team

    result = recommend_mission_team("routing recovery", "recovery")
    assert result.lead == "Fox"
    assert result.deputy == "Dozer"
    assert result.challenger == "Shere Khan"
    assert result.verifier == "The Twins"
    assert result.recovery is None
    assert result.status == "PROPOSED_UNVERIFIED"
    assert not result.passport_verified
    assert not result.permissions_verified
    assert not result.evidence_verified
    assert not result.agent_execution_verified
    assert not result.grants_permissions
    assert result.human_authority_final


def test_mission_selection_rejects_unknown_and_invalid_depth():
    from oap.smi.protocol_selection import recommend_mission_team

    for mission, protocol, depth in [
        ("routing", "unknown", "AUTO"),
        ("", "recovery", "AUTO"),
        ("routing", "recovery", "unsafe"),
        (None, "recovery", "AUTO"),
    ]:
        result = recommend_mission_team(mission, protocol, depth)
        assert result.lead is None
        assert result.status == "UNRECOGNISED"
        assert not result.grants_permissions


def test_small_depth_does_not_assign_unneeded_reviewers():
    from oap.smi.protocol_selection import recommend_mission_team

    result = recommend_mission_team("small change", "creation", "3")
    assert result.lead == "NIRMATA"
    assert result.deputy == "Architect"
    assert result.specialists == ()
    assert result.challenger is None
    assert result.verifier is None


def test_candidate_eligibility_fails_closed_without_passport():
    from oap.smi.protocol_selection import check_mission_candidate_eligibility

    class Registry:
        def passport(self, agent_id):
            return None

    result = check_mission_candidate_eligibility("FOX-001", Registry())
    assert result["eligible"] is False
    assert result["reason"] == "PASSPORT_NOT_FOUND"
    assert result["grants_permissions"] is False


def test_candidate_eligibility_requires_active_permission_and_audit():
    from oap.smi.protocol_selection import check_mission_candidate_eligibility

    class Registry:
        def __init__(self, passport):
            self.record = passport

        def passport(self, agent_id):
            return self.record

    passport = {
        "agent_id": "FOX-001", "status": "ACTIVE",
        "permissions": ["ANALYSE"], "audit_required": True,
        "family_id": "recovery", "guardian": "Guardian",
        "memory": {}, "restrictions": [],
    }
    allowed = check_mission_candidate_eligibility("FOX-001", Registry(passport))
    assert allowed["eligible"] is True
    assert allowed["execution_verified"] is False
    assert allowed["performance_verified"] is False
    for update in (
        {"status": "INACTIVE"},
        {"permissions": []},
        {"audit_required": False},
    ):
        denied = check_mission_candidate_eligibility("FOX-001", Registry({**passport, **update}))
        assert denied["eligible"] is False


def test_candidate_eligibility_rejects_mismatched_identity_or_registry():
    from oap.smi.protocol_selection import check_mission_candidate_eligibility

    class Registry:
        def passport(self, agent_id):
            return {"agent_id": "OTHER", "status": "ACTIVE", "permissions": ["ANALYSE"]}

    assert not check_mission_candidate_eligibility("FOX-001", Registry())["eligible"]
    assert not check_mission_candidate_eligibility("FOX-001", object())["eligible"]


def test_team_screening_does_not_assume_names_are_passport_ids():
    from oap.smi.protocol_selection import recommend_mission_team, screen_mission_team_candidates

    team = recommend_mission_team("routing", "recovery")
    screened = screen_mission_team_candidates(team, object())
    assert screened["all_eligible"] is False
    assert screened["candidates"]["Fox"]["reason"] == "PASSPORT_ID_UNRESOLVED"
    assert screened["agent_execution_verified"] is False
    assert screened["founder_final_required"] is True


def test_team_screening_partial_eligibility_never_promotes_team():
    from oap.smi.protocol_selection import recommend_mission_team, screen_mission_team_candidates

    class Registry:
        def passport(self, agent_id):
            return {
                "agent_id": agent_id, "status": "ACTIVE",
                "permissions": ["ANALYSE"], "audit_required": True,
                "family_id": "recovery", "guardian": "Guardian",
                "memory": {}, "restrictions": [],
            }

    team = recommend_mission_team("routing", "recovery", "3")
    screened = screen_mission_team_candidates(team, Registry(), agent_ids={"Fox": "FOX-001"})
    assert screened["candidates"]["Fox"]["eligible"] is True
    assert screened["candidates"]["Dozer"]["eligible"] is False
    assert screened["all_eligible"] is False
    assert screened["grants_permissions"] is False
