from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_final_source_review_gate():
    doc = (ROOT / "docs/SMI_CHAT_PRODUCT_COMPLETION.md").read_text()
    assert "live handset proof" in doc
