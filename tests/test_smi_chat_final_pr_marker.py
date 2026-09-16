from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_final_pr_marker():
    assert (ROOT / "docs/SMI_CHAT_PRODUCT_COMPLETION.md").exists()
