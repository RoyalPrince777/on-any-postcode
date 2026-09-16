from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_ci_contract_complete():
    assert (ROOT / "tests/test_smi_chat_product_gate.py").exists()
    assert (ROOT / "tests/test_smi_chat_product_done_source.py").exists()
