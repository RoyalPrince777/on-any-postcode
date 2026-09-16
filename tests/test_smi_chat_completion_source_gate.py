from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_final_source_gate():
    wrapper = (ROOT / "mission_control/templates/ollama_chat.html").read_text()
    base = (ROOT / "mission_control/templates/ollama_chat_base.html").read_text()
    controller = (ROOT / "mission_control/static/smi_canonical_controller.js").read_text()
    identity = (ROOT / "mission_control/static/smi_product_identity.js").read_text()
    doc = (ROOT / "docs/SMI_CHAT_PRODUCT_COMPLETION.md").read_text()

    assert "Sovereign Megaverse Intelligence" in wrapper
    assert "SMI AUTO" in identity
    assert "singleSubmitOwner:true" in controller
    assert "studioDuplicate:false" in controller
    assert "warRoomUrl" in wrapper and "signalsUrl" in wrapper
    assert "guardianUrl" in wrapper and "hrmUrl" in wrapper
    assert "getUserMedia" in controller and "getDisplayMedia" in controller
    assert "SpeechRecognition" in controller and "speechSynthesis" in controller
    assert "AbortController" in controller
    assert 'id="media-input"' in base and 'id="image-input"' in base
    assert "@media(max-width:820px)" in base
    assert "live handset proof" in doc
    assert "does not change Founder authentication" in doc
