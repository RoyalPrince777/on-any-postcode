from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_source_complete_review():
    doc = (ROOT / "docs/SMI_CHAT_PRODUCT_COMPLETION.md").read_text()
    assert "Canonical ownership" in doc
    assert "Product truth" in doc
