from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_source_build_complete_final():
    assert (ROOT / "mission_control/static/smi_product_identity.js").exists()
    assert (ROOT / "tests/test_smi_chat_product_gate.py").exists()
