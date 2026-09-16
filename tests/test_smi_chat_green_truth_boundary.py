from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_source_completion_does_not_claim_production_green():
    doc = (ROOT / "docs/SMI_CHAT_PRODUCT_COMPLETION.md").read_text().lower()
    assert "live handset proof" in doc
    assert "production-proven" in doc
    assert "source-level passing test is not a substitute" in doc
