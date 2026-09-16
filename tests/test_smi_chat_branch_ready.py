from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_source_slice_is_ready_for_governed_ci_not_declared_live():
    doc = (ROOT / "docs/SMI_CHAT_PRODUCT_COMPLETION.md").read_text()
    assert "source-level passing test is not a substitute for live handset proof" in doc
    assert "production-proven" in doc
