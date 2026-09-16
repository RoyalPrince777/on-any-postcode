from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_build_gate_final_closed():
    identity = (ROOT / "mission_control/static/smi_product_identity.js").read_text()
    assert "SMI AUTO" in identity
