from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_ready_to_open_pr():
    assert (ROOT / "tests/test_smi_chat_product_gate.py").exists()
    assert (ROOT / "tests/test_smi_chat_final_source_complete.py").exists()
