from mission_control import smi_chat_runtime


def test_explicit_continue_resumes_latest_governed_request():
    prompt, continuation = smi_chat_runtime._core._continuation_prompt(
        original="🟣",
        history=[
            {"role": "user", "content": "Deep dive the SMI to War Room handoff."},
            {"role": "assistant", "content": "The bounded handoff is implemented."},
        ],
        context={
            "request_id": "11111111-1111-4111-8111-111111111199",
            "task_type": "TECHNICAL",
            "summary": "Bounded handoff implemented; exact-head proof pending.",
            "output_state": "REVIEW_REQUIRED",
            "signal_level": "PURPLE",
        },
    )

    assert continuation["active"] is True
    assert continuation["resumed_request_id"] == "11111111-1111-4111-8111-111111111199"
    assert continuation["resumed_output_state"] == "REVIEW_REQUIRED"
    assert continuation["task_type"] == "TECHNICAL"
    assert prompt.startswith("CONTINUE CURRENT BOUNDED MISSION.")
    assert "Deep dive the SMI to War Room handoff." in prompt
    assert "REVIEW_REQUIRED" in prompt


def test_continue_without_prior_request_does_not_invent_context():
    prompt, continuation = smi_chat_runtime._core._continuation_prompt(
        original="🟣",
        history=[],
        context=None,
    )

    assert prompt == "🟣"
    assert continuation["active"] is False
    assert continuation["resumed_request_id"] is None
    assert continuation["resumed_output_state"] is None


def test_continuation_recognition_is_explicit_not_keyword_guessing():
    assert smi_chat_runtime._core._is_continuation_command("continue") is True
    assert smi_chat_runtime._core._is_continuation_command("🟣") is True
    assert smi_chat_runtime._core._is_continuation_command(
        "continue explaining how the protocol works"
    ) is False
