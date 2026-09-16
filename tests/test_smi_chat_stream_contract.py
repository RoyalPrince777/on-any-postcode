from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_canonical_controller_uses_governed_stream_and_csrf():
    text = (ROOT / "mission_control/static/smi_canonical_controller.js").read_text()
    assert "fetch(streamUrl" in text
    assert "'X-OAP-CSRF':csrfToken" in text
    assert "credentials:'same-origin'" in text
    assert "AbortController" in text
    assert "oap-smi-complete" in text


def test_stream_completion_records_conversation_and_clears_attachments():
    text = (ROOT / "mission_control/static/smi_canonical_controller.js").read_text()
    assert "conversationId=completeResult.conversation_id" in text
    assert "clearAttachments()" in text
    assert "loadConversations()" in text
