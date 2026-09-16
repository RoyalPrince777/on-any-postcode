from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_completed_stream_requires_recorded_result_before_success_state():
    controller = (ROOT / "mission_control/static/smi_canonical_controller.js").read_text()
    assert "if(!completeResult)throw new Error('The governed response did not finish recording.')" in controller
    assert "Ready · governed result recorded" in controller
