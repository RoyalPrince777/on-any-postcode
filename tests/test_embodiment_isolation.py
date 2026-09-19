from __future__ import annotations

import pytest

from mission_control import embodiment_isolation, smi_proof_gate


def test_each_embodiment_channel_isolates_without_killing_smi_chat():
    controller = embodiment_isolation.EmbodimentIsolationController("session-a")

    for channel in embodiment_isolation.CHANNELS:
        before = dict(controller.channels)
        state = controller.isolate(channel, reason="test_fault")

        assert state["channels"][channel] == "ISOLATED"
        assert state["smi_chat_available"] is True
        assert state["brain_alive"] is True
        for other in embodiment_isolation.CHANNELS:
            if other != channel:
                assert state["channels"][other] == before[other]

        controller.recover(
            channel,
            proof_ref=f"proof:{channel.lower()}",
            human_reenable=channel == "CAPTURE",
        )


def test_capture_recovery_requires_explicit_human_reenable():
    controller = embodiment_isolation.EmbodimentIsolationController("session-b")
    controller.isolate("CAPTURE")

    with pytest.raises(PermissionError, match="capture_human_reenable_required"):
        controller.recover("CAPTURE", proof_ref="camera-safe")

    recovered = controller.recover(
        "CAPTURE",
        proof_ref="camera-safe",
        human_reenable=True,
    )
    assert recovered["channels"]["CAPTURE"] == "ACTIVE"


def test_recovery_without_proof_fails_closed():
    controller = embodiment_isolation.EmbodimentIsolationController("session-c")
    controller.isolate("VOICE")

    with pytest.raises(PermissionError, match="recovery_proof_required"):
        controller.recover("VOICE", proof_ref="")


def test_master_stop_isolates_body_but_preserves_brain_and_chat():
    controller = embodiment_isolation.EmbodimentIsolationController("session-d")

    state = controller.master_stop()

    assert set(state["isolated_channels"]) == set(embodiment_isolation.CHANNELS)
    assert state["smi_chat_available"] is True
    assert state["brain_alive"] is True
    assert state["independent_execution"] is False


def test_bounded_embodiment_isolation_recovery_proof_passes():
    proof = embodiment_isolation.bounded_isolation_recovery_proof()

    assert proof["passed"] is True
    assert all(proof["independent_isolation"].values())
    assert proof["master_stop_contained"] is True
    assert all(proof["recovery"].values())
    assert proof["restored"] is True
    assert proof["smi_chat_survived"] is True
    assert proof["production_state_mutated"] is False
    assert proof["execution_authority_expanded"] is False



def test_canonical_aegis_gate_consumes_embodiment_isolation_proof():
    proof = smi_proof_gate._isolation_recovery_exercise()

    assert proof["passed"] is True
    assert proof["embodiment_channels_independent"] is True
    assert proof["embodiment_master_stop_contained"] is True
    assert proof["embodiment_recovery_proven"] is True
    assert proof["smi_chat_survived_body_isolation"] is True
