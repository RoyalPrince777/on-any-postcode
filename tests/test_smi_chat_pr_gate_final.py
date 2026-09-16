from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_pr_gate_final():
    assert (ROOT / "tests/test_smi_chat_product_gate.py").exists()
    assert (ROOT / "tests/test_smi_chat_build_finalized.py").exists()
