from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_completion_change_is_additive_to_existing_chat_engine():
    wrapper = (ROOT / "mission_control/templates/ollama_chat.html").read_text()
    identity = (ROOT / "mission_control/static/smi_product_identity.js").read_text()
    assert "smi_product_identity.js" in wrapper
    assert "singleSubmitOwner" not in identity
    assert "fetch(" not in identity
    assert "getUserMedia" not in identity
