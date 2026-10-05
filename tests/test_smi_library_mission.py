"""SMI Library mission status is computed from explicit evidence checks."""

from mission_control import smi_library_mission


def test_library_mission_percentage_is_computed_not_hand_entered():
    status = smi_library_mission.status()
    passed = sum(1 for item in status["checks"] if item["passed"])
    total = len(status["checks"])

    assert status["passed"] == passed
    assert status["total"] == total
    assert status["evidence_percentage"] == round((passed / total) * 100)
    assert status["ci_green"] is False
    assert status["runtime_image_green"] is False
    assert status["governed_checks_green"] is False
    assert status["live_payment_claimed"] is False
    assert status["production_green"] is False
