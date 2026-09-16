from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_smi_chat_product_gate_source_contract():
    wrapper = (ROOT / "mission_control/templates/ollama_chat.html").read_text()
    base = (ROOT / "mission_control/templates/ollama_chat_base.html").read_text()
    controller = (ROOT / "mission_control/static/smi_canonical_controller.js").read_text()
    identity = (ROOT / "mission_control/static/smi_product_identity.js").read_text()

    checks = {
        "single_smi": "Sovereign Megaverse Intelligence" in wrapper,
        "auto": "SMI AUTO" in identity,
        "chat": 'id="chat-form"' in base and "fetch(streamUrl" in controller,
        "history": 'id="history-list"' in base,
        "files": 'id="file-button"' in base,
        "images": 'id="image-button"' in base,
        "voice": "SpeechRecognition" in controller and "speechSynthesis" in controller,
        "camera": "getUserMedia" in controller,
        "screen": "getDisplayMedia" in controller,
        "stop": "oapAbort.abort()" in controller,
        "mobile": "@media(max-width:820px)" in base and "height:100dvh" in base,
        "war_room": "warRoomUrl" in wrapper,
        "signals": "signalsUrl" in wrapper,
        "guardian": "guardianUrl" in wrapper,
        "hrm": "hrmUrl" in wrapper,
        "function_health": "functionHealthUrl" in wrapper,
        "green_gate": "greenGateUrl" in wrapper,
        "no_studio_duplicate": "studioDuplicate:false" in controller,
    }
    assert all(checks.values()), [name for name, passed in checks.items() if not passed]
