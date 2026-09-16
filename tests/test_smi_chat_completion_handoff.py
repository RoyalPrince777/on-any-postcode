from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_completion_handoff_is_bounded():
    doc = (ROOT / "docs/SMI_CHAT_PRODUCT_COMPLETION.md").read_text()
    assert "Scope lock" in doc
    assert "Founder authentication" in doc
    assert "live handset proof" in doc
