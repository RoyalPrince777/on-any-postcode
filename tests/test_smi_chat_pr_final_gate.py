from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_pr_final_gate():
    assert (ROOT / "tests/test_smi_chat_product_gate.py").exists()
    assert (ROOT / "tests/test_smi_chat_build_final.py").exists()
