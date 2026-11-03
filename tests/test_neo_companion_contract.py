"""Focused contract checks for Neo's seven-lane companion projection."""

from mission_control import matrix_signal_bus


def test_neo_companion_seven_lanes_are_unique_and_bounded():
    profile = matrix_signal_bus.neo_companion_profile()
    lanes = profile["capabilities"]
    assert len(lanes) == 7
    assert {lane["id"] for lane in lanes} == {
        "intelligence", "engineering", "dialogue", "avatar",
        "movement", "communication", "defence",
    }
    assert profile["home"]["group_id"] == "nebuchadnezzar"
    assert not profile["independent_execution_granted"]
    assert not profile["certified"]
    assert profile["founder_final_required"]
    assert profile["guardian_required"]


def test_neo_companion_does_not_claim_unverified_runtime():
    profile = matrix_signal_bus.topology()["neo_companion"]
    assert profile["matrix_signal_bus_available"]
    assert not profile["real_agent_message_delivery_verified"]
    assert not profile["persona"]["dialogue_model_connected"]
    assert not profile["presentation"]["avatar_runtime_verified"]
    assert not profile["presentation"]["movement_runtime_verified"]
    assert "static_fallback" in profile["presentation"]["modes"]
    assert all(lane["evidence_state"] != "runtime_verified" for lane in profile["capabilities"])


def test_neo_review_response_is_grounded_not_autonomous():
    response = matrix_signal_bus.neo_review_response(
        topic="Inspect Android Home evidence",
        evidence=("Exact-head CI pending", "Physical device receipt missing"),
        blocked=True,
    )
    assert response["speaker"] == "Neo"
    assert "Exact-head CI pending" in response["message"]
    assert "HOLD" in response["message"]
    assert not response["model_generated"]
    assert not response["voice_generated"]
    assert not response["avatar_animation_triggered"]
    assert not response["execution_granted"]
    assert response["founder_final_required"]


def test_neo_review_response_no_evidence_is_not_green():
    response = matrix_signal_bus.neo_review_response(topic="Assess readiness")
    assert "No verified evidence supplied" in response["message"]
    assert "unverified" in response["message"]


def test_neo_review_response_rejects_unbounded_inputs():
    import pytest

    with pytest.raises(TypeError):
        matrix_signal_bus.neo_review_response(topic="Test", evidence="forged proof")
    with pytest.raises(ValueError):
        matrix_signal_bus.neo_review_response(topic="Test", evidence=("x",) * 8)
    with pytest.raises(ValueError):
        matrix_signal_bus.neo_review_response(topic=" ")
    with pytest.raises(TypeError):
        matrix_signal_bus.neo_review_response(topic="Test", blocked="yes")
