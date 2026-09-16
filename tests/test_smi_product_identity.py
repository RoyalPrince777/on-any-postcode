from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_smi_identity_is_loaded_before_chat_controllers():
    page = (ROOT / "mission_control/templates/ollama_chat.html").read_text()
    identity = "smi_product_identity.js"
    controller = "smi_chat_final.js"
    assert identity in page
    assert page.index(identity) < page.index(controller)


def test_smi_identity_uses_canonical_message_label():
    script = (ROOT / "mission_control/static/smi_product_identity.js").read_text()
    assert "Sovereign Megaverse Intelligence" in script
    assert "Message SMI" in script
    assert "SMI intelligence state" in script
    assert "duplicateMindIdentity:false" in script
