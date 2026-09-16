from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_source_review_contract_complete():
    doc = (ROOT / "docs/SMI_CHAT_PRODUCT_COMPLETION.md").read_text()
    assert "Canonical ownership" in doc
    assert "Product truth" in doc
    assert "Scope lock" in doc
