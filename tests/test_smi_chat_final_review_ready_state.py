from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_final_review_ready_state():
    assert (ROOT / "mission_control/static/smi_product_identity.js").exists()
