import pytest

from mission_control.war_room_evidence_review import project_mission_evidence

SHA = "a" * 40


def test_projection_does_not_fabricate_votes_or_green():
    result = project_mission_evidence(
        mission="OAP ARM64", revision=SHA,
        checks={"pytest": {"status": "passed", "revision": SHA}},
    )
    assert result["checks_passed"] == 1
    assert result["judge_votes"] is None
    assert result["full_green"] is False
    assert result["external_checks_authenticated"] is False
    assert len(result["canonical_judges"]) == 7


@pytest.mark.parametrize("checks", [
    {"pytest": {"status": "passed", "revision": "b" * 40}},
    {"pytest": {"status": "GREEN", "revision": SHA}},
    {"pytest": {"status": "unknown", "revision": SHA}},
])
def test_mismatch_or_unverified_status(checks):
    if checks["pytest"]["status"] == "unknown":
        result = project_mission_evidence(mission="OAP", revision=SHA, checks=checks)
        assert result["blocking_checks"] == ["pytest"]
    else:
        with pytest.raises(ValueError):
            project_mission_evidence(mission="OAP", revision=SHA, checks=checks)


def test_missing_receipts_are_not_green():
    result = project_mission_evidence(mission="OAP", revision=SHA, checks={})
    assert result["checks_total"] == 0
    assert result["full_green"] is False


def test_revision_required():
    with pytest.raises(ValueError):
        project_mission_evidence(mission="OAP", revision="main", checks={})
