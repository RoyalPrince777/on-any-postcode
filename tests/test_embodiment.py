from __future__ import annotations

import pytest

from mission_control import embodiment, smi_cancellation, smi_chat_runtime


def test_embodiment_is_one_smi_presentation_layer_not_an_execution_authority():
    status = embodiment.status()

    assert status["intelligence_owner"] == "SMI"
    assert status["brain_count_added"] == 0
    assert status["independent_intelligence"] is False
    assert status["independent_execution"] is False
    assert status["execution_state_exposed"] is False
    assert "EXECUTE" not in status["authority_states"]
    assert status["human_authority_final"] is True


def test_truth_signal_controls_expression_and_unknown_truth_fails_to_warning():
    controller = embodiment.EmbodimentController("session-1")

    warning = controller.present(
        speech="Evidence is incomplete.",
        truth_signal="warning",
        authority_state="RECOMMENDATION",
        motor_intent="EXPLAIN",
    )
    assert warning["truth"]["id"] == "warning"
    assert warning["truth"]["expression"] == "MEASURED"

    unknown = controller.present(truth_signal="not-a-real-truth-state")
    assert unknown["truth"]["id"] == "warning"
    assert unknown["truth"]["expression"] != "CALM_POSITIVE"


def test_stop_overrides_body_output_and_requires_explicit_human_restart():
    controller = embodiment.EmbodimentController(
        "session-2", capture_allowed=True
    )
    controller.present(
        speech="Speaking.",
        truth_signal="healthy",
        authority_state="INFORMATION",
        motor_intent="SPEAK",
        panel_refs=("WAR_ROOM_STATUS",),
    )

    stopped = controller.stop()
    assert stopped["state"] == "STOPPED"
    assert stopped["motor_intent"] == "STOP"
    assert stopped["speech"] == ""
    assert stopped["panel_refs"] == ()
    assert stopped["capture_allowed"] is False
    assert controller.stop()["state"] == "STOPPED"

    with pytest.raises(PermissionError, match="human_restart_required"):
        controller.present(speech="Must not resume itself.")

    restarted = controller.transition("IDLE", human_restart=True)
    assert restarted["state"] == "IDLE"


def test_unknown_motor_intent_fails_closed():
    controller = embodiment.EmbodimentController("session-3")

    with pytest.raises(ValueError, match="invalid_motor_intent"):
        controller.present(motor_intent="RAW_JOINT_OVERRIDE")


def test_founder_only_context_cannot_render_to_public_surface():
    controller = embodiment.EmbodimentController("session-4")

    with pytest.raises(PermissionError, match="embodiment_privacy_scope_blocked"):
        controller.present(
            speech="Founder private data",
            privacy_scope="FOUNDER_ONLY",
            presentation_scope="PUBLIC",
        )

    state = controller.snapshot()
    assert state["state"] == "BLOCKED"
    assert state["authority_state"] == "BLOCKED"
    assert state["speech"] == ""
    assert state["panel_refs"] == ()


def test_degraded_embodiment_falls_back_without_creating_another_brain():
    controller = embodiment.EmbodimentController("session-5")

    assert controller.degrade()["fallback_mode"] == "REDUCED"
    assert controller.degrade()["fallback_mode"] == "VOICE"
    text = controller.degrade()
    assert text["fallback_mode"] == "TEXT"
    assert text["motor_intent"] == "REST"
    assert text["brain_count_added"] == 0


def test_cancelled_worker_can_never_emit_normal_completion(monkeypatch):
    def fake_chat(*args, cancellation_token=None, **kwargs):
        assert cancellation_token is not None
        cancellation_token.cancel("human_stop")
        cancellation_token.raise_if_cancelled()

    monkeypatch.setattr(smi_chat_runtime, "chat", fake_chat)
    events = list(smi_chat_runtime.chat_events("status", "founder", "Founder"))

    assert any(item["type"] == "cancelled" for item in events)
    assert not any(item["type"] == "complete" for item in events)


def test_cancelled_token_prevents_commit_gate():
    class Connection:
        committed = False

        def commit(self):
            self.committed = True

    connection = Connection()
    token = smi_cancellation.new_token("founder")
    token.cancel("human_stop")

    with pytest.raises(smi_cancellation.SMIRequestCancelled):
        smi_chat_runtime._core._commit_if_not_cancelled(connection, token)

    assert connection.committed is False
