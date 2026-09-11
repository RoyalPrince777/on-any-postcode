from pathlib import Path


def test_smi_chat_wrapper_does_not_fake_provider_success():
    text = Path("mission_control/templates/ollama_chat.html").read_text(encoding="utf-8")
    assert "item.ready?'green':'yellow'" in text
    assert "Setup needed. Credentials are never shown." in text
    assert "Truth gate attention" in text


def test_smi_chat_receipt_is_bound_to_completed_stream_result():
    text = Path("mission_control/templates/ollama_chat.html").read_text(encoding="utf-8")
    assert "event: complete" in text
    assert "oap-smi-complete" in text
    assert "Recorded result" not in text  # avoid unproven cosmetic copy
    assert "Shown only after the governed response completed" in text
