from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_source_completion_locked():
    controller = (ROOT / "mission_control/static/smi_canonical_controller.js").read_text()
    assert "singleSubmitOwner:true" in controller
    assert "studioDuplicate:false" in controller
