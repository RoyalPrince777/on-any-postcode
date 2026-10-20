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
