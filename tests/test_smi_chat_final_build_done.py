from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_final_build_done():
    assert (ROOT / "mission_control/static/smi_product_identity.js").exists()
