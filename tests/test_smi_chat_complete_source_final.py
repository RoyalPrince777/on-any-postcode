from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_complete_source_final():
    assert (ROOT / "mission_control/static/smi_product_identity.js").exists()
    assert (ROOT / "docs/SMI_CHAT_PRODUCT_COMPLETION.md").exists()
