from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_last_source_gate():
    doc = (ROOT / "docs/SMI_CHAT_PRODUCT_COMPLETION.md").read_text()
    assert "SMI Chat is the private Founder front door" in doc
    assert "live handset proof" in doc
