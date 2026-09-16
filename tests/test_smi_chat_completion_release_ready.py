from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_completion_release_ready_source_only():
    doc = (ROOT / "docs/SMI_CHAT_PRODUCT_COMPLETION.md").read_text()
    assert "live handset proof" in doc
    assert "source-level passing test" in doc
