from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_voice_input_has_permission_and_elapsed_states():
    text = (ROOT / "mission_control/static/smi_canonical_controller.js").read_text()
    assert "Microphone permission required" in text
    assert "Microphone permission blocked" in text
    assert "Listening · ${oapElapsed()}s" in text
    assert "Voice captured · edit or send" in text


def test_voice_reply_can_be_disabled():
    text = (ROOT / "mission_control/static/smi_canonical_controller.js").read_text()
    assert "Voice reply on" in text
    assert "Voice reply off" in text
    assert "aria-pressed" in text
