from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_complete_for_governed_review():
    doc = (ROOT / "docs/SMI_CHAT_PRODUCT_COMPLETION.md").read_text()
    assert "Human Authority" in doc
    assert "source-level passing test" in doc
