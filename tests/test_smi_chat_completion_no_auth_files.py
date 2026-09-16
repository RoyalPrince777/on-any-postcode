from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_completion_assets_do_not_contain_auth_mutation_language():
    identity = (ROOT / "mission_control/static/smi_product_identity.js").read_text().lower()
    doc = (ROOT / "docs/SMI_CHAT_PRODUCT_COMPLETION.md").read_text().lower()
    assert "password" not in identity
    assert "authentication" not in identity
    assert "does not change founder authentication" in doc
