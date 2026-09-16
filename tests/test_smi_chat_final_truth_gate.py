from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_final_truth_gate():
    doc = (ROOT / "docs/SMI_CHAT_PRODUCT_COMPLETION.md").read_text()
    assert "source-level passing test" in doc
    assert "live handset proof" in doc
    assert "production-proven" in doc
    assert "Human Authority" in doc
