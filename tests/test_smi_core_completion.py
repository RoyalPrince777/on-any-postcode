from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "mission_control" / "smi_completion_contract.py"


def test_bounded_smi_core_has_explicit_100_percent_contract():
    source = CONTRACT.read_text(encoding="utf-8")
    assert "CORE_PROOF_GATE_IDS" in source
    assert '"founder_chat_interaction"' in source
    assert '"hrm_receipt_chain"' in source
    assert '"green_gate_aggregation"' in source
    assert '"rollback_recovery"' in source
    assert '"observability"' in source
    assert '"percent": core_completion_percent' in source
    assert '"complete": core_complete' in source
    assert '"bounded_core": "green" if core_complete else "proof_required"' in source


def test_higher_autonomy_does_not_fake_block_bounded_core_completion():
    source = CONTRACT.read_text(encoding="utf-8")
    core_block = source.split("CORE_PROOF_GATE_IDS = (", 1)[1].split(")", 1)[0]
    assert "a7_external" not in core_block
    assert '"higher_autonomy_certification_required": False' in source
    assert '"a5_preparation_may_be_enabled": True' in source
    assert '"a6_a7_remain_locked": True' in source
