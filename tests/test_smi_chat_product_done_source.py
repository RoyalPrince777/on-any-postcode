from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_product_source_build_complete():
    identity = (ROOT / "mission_control/static/smi_product_identity.js").read_text()
    wrapper = (ROOT / "mission_control/templates/ollama_chat.html").read_text()
    assert "Sovereign Megaverse Intelligence" in identity
    assert "smi_product_identity.js" in wrapper
