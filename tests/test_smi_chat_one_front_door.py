from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_one_founder_front_door_contract():
    doc = (ROOT / "docs/SMI_CHAT_PRODUCT_COMPLETION.md").read_text()
    identity = (ROOT / "mission_control/static/smi_product_identity.js").read_text()
    assert "SMI Chat is the private Founder front door" in doc
    assert "Sovereign Megaverse Intelligence" in identity
