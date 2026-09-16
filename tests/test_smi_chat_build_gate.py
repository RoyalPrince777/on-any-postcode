from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_build_gate_keeps_source_truth_and_governance():
    doc = (ROOT / "docs/SMI_CHAT_PRODUCT_COMPLETION.md").read_text()
    assert "Human Authority" in doc
    assert "live handset proof" in doc
    assert "does not change Founder authentication" in doc
