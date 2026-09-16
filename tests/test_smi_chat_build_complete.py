from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_bounded_source_build_complete():
    identity = (ROOT / "mission_control/static/smi_product_identity.js").read_text()
    doc = (ROOT / "docs/SMI_CHAT_PRODUCT_COMPLETION.md").read_text()
    assert "SMI AUTO" in identity
    assert "live handset proof" in doc
