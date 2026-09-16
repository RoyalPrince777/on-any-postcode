from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_completion_done_source_contract():
    identity = (ROOT / "mission_control/static/smi_product_identity.js").read_text()
    doc = (ROOT / "docs/SMI_CHAT_PRODUCT_COMPLETION.md").read_text()
    assert "Sovereign Megaverse Intelligence" in identity
    assert "live handset proof" in doc
