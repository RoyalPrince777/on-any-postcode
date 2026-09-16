from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_capture_cleanup_runs_in_finally():
    text = (ROOT / "mission_control/static/smi_canonical_controller.js").read_text()
    capture = text[text.index("async function oapCaptureFrame"):text.index("async function oapCamera")]
    assert "finally" in capture
    assert "stream.getTracks().forEach(track=>track.stop())" in capture
