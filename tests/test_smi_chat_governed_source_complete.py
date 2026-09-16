from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_governed_source_complete():
    doc = (ROOT / "docs/SMI_CHAT_PRODUCT_COMPLETION.md").read_text()
    assert "Guardian and Human Authority remain unchanged" in doc
