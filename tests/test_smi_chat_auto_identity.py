from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_single_auto_identity_has_no_depth_mode_variants():
    identity = (ROOT / "mission_control/static/smi_product_identity.js").read_text()
    assert "SMI AUTO" in identity
    assert "AUTO 3" not in identity
    assert "AUTO 7" not in identity
    assert "AUTO 21" not in identity
    assert "7×7×7" not in identity
