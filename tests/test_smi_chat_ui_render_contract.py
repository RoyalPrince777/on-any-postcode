from pathlib import Path

WRAPPER = Path("mission_control/templates/ollama_chat.html")
JS = Path("mission_control/static/smi_chat_final.js")


def test_smi_chat_wrapper_does_not_fake_provider_success():
    text = JS.read_text(encoding="utf-8")
    assert "item.ready?'green':'yellow'" in text
    assert "Setup needed. Credentials are never shown." in text
    assert "Truth gate attention" in text


def test_smi_chat_receipt_is_bound_to_completed_stream_result():
    text = JS.read_text(encoding="utf-8")
    assert "event: complete" in text
    assert "oap-smi-complete" in text
    assert "Shown only after the governed response completed" in text


def test_smi_chat_wrapper_only_passes_server_generated_routes():
    text = WRAPPER.read_text(encoding="utf-8")
    assert "mission_control.smi_chat_stream" in text
    assert "founder_tools.github_propose_branch" in text
    assert "founder_tools.github_action_approval" in text
    assert "founder_tools.github_execute_approved_action" in text
