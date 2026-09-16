from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_source_finalized():
    identity = (ROOT / "mission_control/static/smi_product_identity.js").read_text()
    assert "SMI AUTO" in identity
    assert "Sovereign Megaverse Intelligence" in identity
