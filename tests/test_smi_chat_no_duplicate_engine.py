from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_identity_layer_is_display_only_not_second_chat_engine():
    text = (ROOT / "mission_control/static/smi_product_identity.js").read_text()
    forbidden = ("fetch(", "WebSocket", "EventSource", "SpeechRecognition", "getUserMedia", "getDisplayMedia")
    for token in forbidden:
        assert token not in text


def test_wrapper_loads_only_existing_canonical_submit_controller():
    text = (ROOT / "mission_control/templates/ollama_chat.html").read_text()
    assert text.count("smi_canonical_controller.js") == 1
    assert text.count("smi_product_identity.js") == 1
