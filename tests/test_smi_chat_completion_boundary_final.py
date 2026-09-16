from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_completion_boundary_is_source_not_runtime_claim():
    doc = (ROOT / "docs/SMI_CHAT_PRODUCT_COMPLETION.md").read_text()
    assert "A source-level passing test is not a substitute for live handset proof" in doc
    assert "before those interactions are called production-proven" in doc
