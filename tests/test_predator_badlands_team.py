"""Contract tests for film-inspired Badlands advisory teamwork."""
from oap.smi.predator_badlands_team import BADLANDS_TEAM, review_plan


def test_team_members_and_no_execution_authority():
    assert {member.character for member in BADLANDS_TEAM} == {
        "dek", "thia", "bud", "kwei", "tessa", "njohrr"
    }
    assert all(member.authority == "advisory" for member in BADLANDS_TEAM)


def test_missing_and_malformed_evidence_fail_closed():
    assert review_plan(None)["reason"] == "NO_VERIFIED_EVIDENCE"
    assert review_plan({})["ready"] is False
    assert review_plan({"source": ""})["reason"] == "INVALID_EVIDENCE"
    assert review_plan({1: "unexpected"})["ready"] is False


def test_supplied_evidence_never_grants_readiness():
    result = review_plan({"diagnostic": "provided"})
    assert result["reason"] == "HUMAN_REVIEW_REQUIRED"
    assert result["ready"] is False
    assert len(result["roles"]) == 6
