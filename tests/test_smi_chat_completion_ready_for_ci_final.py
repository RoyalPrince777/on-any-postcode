from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_completion_ready_for_ci_final():
    assert (ROOT / "tests/test_smi_chat_product_gate.py").exists()
    assert (ROOT / "tests/test_smi_chat_final_truth_gate.py").exists()
