from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_final_ci_marker():
    assert (ROOT / "tests/test_smi_chat_product_gate.py").exists()
    assert (ROOT / "docs/SMI_CHAT_PRODUCT_COMPLETION.md").exists()
