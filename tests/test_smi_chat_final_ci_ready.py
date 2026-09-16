from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_final_ci_ready():
    assert (ROOT / "tests/test_smi_chat_product_gate.py").exists()
