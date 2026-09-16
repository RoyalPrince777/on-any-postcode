from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_attachment_payload_is_sent_through_canonical_stream():
    base = (ROOT / "mission_control/templates/ollama_chat_base.html").read_text()
    controller = (ROOT / "mission_control/static/smi_canonical_controller.js").read_text()
    assert "selectedAttachment" in base
    assert "attachment:selectedAttachment" in controller
    assert "image_data:selectedImage" in controller
    assert "code_mode:codeMode" in controller
