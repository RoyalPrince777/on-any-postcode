from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_ci_ready_marker():
    assert (ROOT / "tests/test_smi_chat_product_gate.py").is_file()
    assert (ROOT / "tests/test_smi_chat_completion_guard.py").is_file()
