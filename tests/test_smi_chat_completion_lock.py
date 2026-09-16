from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_source_completion_contract_is_locked_to_one_smi():
    identity = (ROOT / "mission_control/static/smi_product_identity.js").read_text()
    controller = (ROOT / "mission_control/static/smi_canonical_controller.js").read_text()
    assert "Sovereign Megaverse Intelligence" in identity
    assert "SMI AUTO" in identity
    assert "singleSubmitOwner:true" in controller
    assert "studioDuplicate:false" in controller
