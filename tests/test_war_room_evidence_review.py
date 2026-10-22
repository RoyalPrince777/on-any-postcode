import pytest

from mission_control.war_room_evidence_review import (
    project_mission_evidence,
    unverified_review,
)

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


def test_missing_required_checks_remain_blocking_even_with_a_passing_subset():
    result = project_mission_evidence(
        mission="OAP", revision=SHA,
        checks={"unit": {"status": "passed", "revision": SHA}},
        required_checks=("unit", "live_route", "permission_denial"),
    )
    assert result["missing_checks"] == ["live_route", "permission_denial"]
    assert result["blocking_checks"] == result["missing_checks"]
    assert result["required_check_inventory_supplied"] is True
    assert result["acceptance_inventory_verified"] is False
    assert result["vpi_percent"] is None


def test_all_supplied_checks_passed_cannot_award_stars_votes_or_live_proof():
    result = project_mission_evidence(
        mission="OAP", revision=SHA,
        checks={"pytest": {"status": "passed", "revision": SHA}},
        required_checks=("pytest",),
    )
    assert result["blocking_checks"] == []
    for name in ("full_green", "external_checks_authenticated", "agent_execution_verified",
                 "live_booking_verified", "dispatch_verified", "payment_verified"):
        assert result[name] is False
    assert result["judge_votes"] is None
    assert result["vpi_percent"] is None
    assert len(result["proof_dimensions"]) == 7
    assert all(d["status"] == "not_verified" and not d["star_awarded"]
               for d in result["proof_dimensions"])


@pytest.mark.parametrize("status", ["failed", "pending", "unknown"])
def test_nonpassing_exact_revision_receipt_blocks(status):
    result = project_mission_evidence(
        mission="OAP", revision=SHA,
        checks={"route": {"status": status, "revision": SHA}},
        required_checks=("route",),
    )
    assert result["blocking_checks"] == ["route"]
    assert result["checks_passed"] == 0


@pytest.mark.parametrize("changes,error", [
    ({"mission": None}, ValueError),
    ({"revision": None}, ValueError),
    ({"checks": []}, TypeError),
    ({"checks": {"unit": {"status": [], "revision": SHA}}}, ValueError),
    ({"checks": {1: {}, "unit": {}}}, ValueError),
    ({"checks": {" ": {}}}, ValueError),
    ({"checks": {"unit": None}}, TypeError),
    ({"checks": {"unit": {"status": "skipped", "revision": SHA}}}, ValueError),
    ({"required_checks": ("unit", "unit")}, ValueError),
    ({"required_checks": (" ",)}, ValueError),
    ({"required_checks": ["unit"]}, ValueError),
])
def test_malformed_receipts_fail_closed(changes, error):
    args = {"mission": "OAP", "revision": SHA, "checks": {}}
    args.update(changes)
    with pytest.raises(error):
        project_mission_evidence(**args)


def test_default_has_no_fabricated_revision_or_shared_mutable_evidence():
    first = unverified_review()
    first["proof_dimensions"][0]["star_awarded"] = True
    second = unverified_review()
    assert second["revision"] is None
    assert second["proof_dimensions"][0]["star_awarded"] is False
