from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_pr_submission_gate():
    assert (ROOT / "tests/test_smi_chat_product_gate.py").exists()
    assert (ROOT / "tests/test_smi_chat_final_gate_closed.py").exists()
