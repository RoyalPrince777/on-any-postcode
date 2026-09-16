from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_bounded_build_closed_final():
    assert (ROOT / "mission_control/static/smi_product_identity.js").exists()
