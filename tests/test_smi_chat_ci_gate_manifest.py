from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_ci_gate_manifest_references_completion_contract():
    assert (ROOT / "tests/test_smi_chat_product_gate.py").exists()
    assert (ROOT / "tests/test_smi_chat_source_completion.py").exists()
    assert (ROOT / "tests/test_smi_chat_build_gate.py").exists()
    assert (ROOT / "docs/SMI_CHAT_PRODUCT_COMPLETION.md").exists()
