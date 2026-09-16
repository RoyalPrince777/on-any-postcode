from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_pr_gate_has_identity_contract_tests_and_truth_boundary():
    assert (ROOT / "mission_control/static/smi_product_identity.js").exists()
    assert (ROOT / "tests/test_smi_chat_product_gate.py").exists()
    doc = (ROOT / "docs/SMI_CHAT_PRODUCT_COMPLETION.md").read_text()
    assert "live handset proof" in doc
