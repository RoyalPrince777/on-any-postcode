"""Seven-role mission planning regression contracts."""
from oap.smi.predator_seven_mission import SPECIALISTS, plan_mission


def test_seven_distinct_specialists_and_bounded_assignments():
    assert len(SPECIALISTS) == len({name for name, _ in SPECIALISTS}) == 7
    result = plan_mission("Investigate APK installation", {"device_log": "supplied"})
    assert result["ready"] is False
    assert result["reason"] == "GOVERNED_REVIEW_REQUIRED"
    assert len(result["assignments"]) == 7
    assert all(item.decision == "HUMAN_REVIEW" for item in result["assignments"])


def test_missing_or_malformed_inputs_fail_closed():
    for task, evidence in (
        ("", {"log": "supplied"}),
        ("Investigate", None),
        ("Investigate", {}),
        ("Investigate", {"log": ""}),
        ("Investigate", {"": "supplied"}),
        ("Investigate", {1: "supplied"}),
    ):
        result = plan_mission(task, evidence)
        assert result["ready"] is False
        assert result["assignments"] == ()
