from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_source_gate_complete():
    identity = (ROOT / "mission_control/static/smi_product_identity.js").read_text()
    controller = (ROOT / "mission_control/static/smi_canonical_controller.js").read_text()
    assert "SMI AUTO" in identity
    assert "singleSubmitOwner:true" in controller
