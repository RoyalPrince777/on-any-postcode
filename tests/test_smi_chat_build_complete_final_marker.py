from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_build_complete_final_marker():
    assert (ROOT / "docs/SMI_CHAT_PRODUCT_COMPLETION.md").exists()
