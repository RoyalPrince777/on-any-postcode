"""Bounded SMI naming vote ledger contract tests."""
import pytest

from oap.smi.naming_vote import (
    HISTORICAL_NAMING_ROUNDS,
    NEW_CHALLENGERS,
    NamingRound,
    project_naming_vote,
)


def test_missing_historical_leaders_are_restored_without_reset():
    result = project_naming_vote(HISTORICAL_NAMING_ROUNDS, NEW_CHALLENGERS)
    assert result.candidates[:len(NEW_CHALLENGERS)] == NEW_CHALLENGERS
    assert {"KORADASO", "ALL ENDZ", "KORAKWAN"}.issubset(result.recovered_leaders)
    assert dict(result.historical_wins)["KORADASO"] == 3
    assert result.founder_final_required and result.advisory_only
    assert result.runtime_verified is False


def test_repeated_candidate_and_protected_name_not_duplicated():
    result = project_naming_vote(HISTORICAL_NAMING_ROUNDS, ("KORADASO", "KORADASO", "ALL ENDZ"))
    assert result.candidates.count("KORADASO") == 1
    assert result.candidates.count("ALL ENDZ") == 1


def test_duplicate_agent_ballot_fails_closed():
    bad = NamingRound("bad", ("KORADASO",), (("Neo", "KORADASO"), ("Neo", "KORADASO")))
    with pytest.raises(ValueError, match="duplicate agent"):
        project_naming_vote((bad,), ())


def test_unknown_candidate_fails_closed():
    bad = NamingRound("bad", ("KORADASO",), (("Neo", "NOT IN ROUND"),))
    with pytest.raises(ValueError, match="unknown candidate"):
        project_naming_vote((bad,), ())


def test_no_evidence_or_duplicate_round_fails_closed():
    with pytest.raises(ValueError, match="historical"):
        project_naming_vote((), ("KORADASO",))
    with pytest.raises(ValueError, match="duplicate round"):
        project_naming_vote((HISTORICAL_NAMING_ROUNDS[0], HISTORICAL_NAMING_ROUNDS[0]), ())


def test_no_authenticated_agent_ballots_are_implied():
    bad = NamingRound("live", ("KORADASO",), provenance="agent_executed")
    with pytest.raises(ValueError, match="provenance"):
        project_naming_vote((bad,), ())
