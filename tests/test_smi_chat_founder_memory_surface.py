from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_conversation_continuity_controls_remain_present():
    base = (ROOT / "mission_control/templates/ollama_chat_base.html").read_text()
    controller = (ROOT / "mission_control/static/smi_canonical_controller.js").read_text()
    assert 'id="new-chat"' in base
    assert 'id="history-list"' in base
    assert "conversation_id:conversationId" in controller
    assert "loadConversations()" in controller


def test_hrm_endpoint_remains_available_to_smi_surface():
    wrapper = (ROOT / "mission_control/templates/ollama_chat.html").read_text()
    assert "hrmUrl" in wrapper
