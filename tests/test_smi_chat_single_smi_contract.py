from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_one_smi_contract_is_visible_and_studio_stays_canonical():
    wrapper = (ROOT / "mission_control/templates/ollama_chat.html").read_text()
    identity = (ROOT / "mission_control/static/smi_product_identity.js").read_text()
    doc = (ROOT / "docs/SMI_CHAT_PRODUCT_COMPLETION.md").read_text()
    assert "Sovereign Megaverse Intelligence" in wrapper
    assert "SMI AUTO" in identity
    assert "OAP Studio Intelligence remains the canonical media intelligence engine" in doc
    assert "SMI Chat is the private Founder front door" in doc
