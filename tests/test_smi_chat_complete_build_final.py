from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_complete_build_final():
    identity = (ROOT / "mission_control/static/smi_product_identity.js").read_text()
    assert "SMI AUTO" in identity
