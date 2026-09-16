from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_smi_chat_final_product_contract():
    wrapper = (ROOT / "mission_control/templates/ollama_chat.html").read_text()
    identity = (ROOT / "mission_control/static/smi_product_identity.js").read_text()
    controller = (ROOT / "mission_control/static/smi_canonical_controller.js").read_text()
    doc = (ROOT / "docs/SMI_CHAT_PRODUCT_COMPLETION.md").read_text()
    assert "Sovereign Megaverse Intelligence" in wrapper
    assert "SMI AUTO" in identity
    assert "singleSubmitOwner:true" in controller
    assert "studioDuplicate:false" in controller
    assert "Human Authority" in doc
    assert "live handset proof" in doc
