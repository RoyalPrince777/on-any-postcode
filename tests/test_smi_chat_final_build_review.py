from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_final_build_review():
    doc = (ROOT / "docs/SMI_CHAT_PRODUCT_COMPLETION.md").read_text()
    assert "Product truth" in doc
    assert "Scope lock" in doc
