from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_stop_aborts_generation_voice_and_mic():
    text = (ROOT / "mission_control/static/smi_canonical_controller.js").read_text()
    assert "oapAbort.abort()" in text
    assert "oapRecognition.stop()" in text
    assert "window.speechSynthesis.cancel()" in text
    assert "Response stopped by Human Authority" in text
