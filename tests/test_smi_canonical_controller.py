from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WRAPPER = ROOT / "mission_control" / "templates" / "ollama_chat.html"
CONTROLLER = ROOT / "mission_control" / "static" / "smi_canonical_controller.js"


def test_canonical_controller_loads_before_legacy_request_guard():
    wrapper = WRAPPER.read_text(encoding="utf-8")
    assert wrapper.count("smi_canonical_controller.js") == 1
    assert wrapper.index("smi_chat_final.js") < wrapper.index("smi_canonical_controller.js")
    assert wrapper.index("smi_chat_compat.js") < wrapper.index("smi_canonical_controller.js")
    assert wrapper.index("smi_canonical_controller.js") < wrapper.index("smi_request_guard.js")


def test_canonical_controller_owns_one_submit_path_fail_closed():
    text = CONTROLLER.read_text(encoding="utf-8")
    assert "let oapLocked=false" in text
    assert "if(oapLocked||oapSend.disabled)return" in text
    assert "oapInput.addEventListener('keydown'" in text
    assert "oapForm.addEventListener('submit'" in text
    assert text.count("event.stopImmediatePropagation()") >= 4
    assert "oapSubmit();" in text
    assert "window.OAP_SMI_CANONICAL" in text
    assert "singleSubmitOwner:true" in text


def test_canonical_controller_owns_voice_mic_and_stop():
    text = CONTROLLER.read_text(encoding="utf-8")
    assert "window.SpeechRecognition||window.webkitSpeechRecognition" in text
    assert "SpeechSynthesisUtterance" in text
    assert "oapVoiceEnabled" in text
    assert "Microphone permission blocked" in text
    assert "Listening · ${oapElapsed()}s" in text
    assert "aria-pressed" in text
    assert "oapAbort.abort()" in text
    assert "speechSynthesis.cancel()" in text
    assert "micOwner:true" in text
    assert "voiceOwner:true" in text
    assert "stopOwner:true" in text


def test_canonical_controller_reuses_media_path_for_camera_and_screen():
    text = CONTROLLER.read_text(encoding="utf-8")
    assert "navigator.mediaDevices?.getUserMedia" in text
    assert "navigator.mediaDevices?.getDisplayMedia" in text
    assert "getVideoTracks" in text
    assert "track.stop()" in text
    assert "oapSetCapturedImage" in text
    assert "routed through existing image/Studio path" in text
    assert "Camera permission blocked" in text
    assert "Screen sharing unavailable on this device" in text
    assert "cameraCapture:true" in text
    assert "screenCapture:true" in text
    assert "studioDuplicate:false" in text


def test_canonical_controller_preserves_governed_backend_contract():
    text = CONTROLLER.read_text(encoding="utf-8")
    assert "streamUrl" in text
    assert "'X-OAP-CSRF':csrfToken" in text
    assert "credentials:'same-origin'" in text
    assert "event: complete" not in text
    assert "oap-smi-complete" in text
    assert "Human Authority" in text
