from pathlib import Path

CONTROLLER = Path("mission_control/static/smi_canonical_controller.js")
COLLECTOR = Path("mission_control/static/smi_android_live_evidence.js")
MOTION = Path("mission_control/static/smi_source_pixel_motion.js")
TEMPLATE = Path("mission_control/templates/ollama_chat.html")
VIEWS = Path("mission_control/views.py")


def test_android_live_evidence_is_real_event_driven_and_private():
    controller = CONTROLLER.read_text(encoding="utf-8")
    collector = COLLECTOR.read_text(encoding="utf-8")
    motion = MOTION.read_text(encoding="utf-8")
    template = TEMPLATE.read_text(encoding="utf-8")
    views = VIEWS.read_text(encoding="utf-8")

    assert "oap-smi-submit-start" in controller
    assert "oap-smi-human-stop" in controller
    assert "oap-smi-background-stop" in controller
    assert "localReplyAudio:oapLocalPlayer?.snapshot?.()" in controller
    assert "physicalAndroidEvidenceEvents:true" in controller

    for required in [
        "oap-smi-character-state",
        "oap-smi-submit-start",
        "oap-smi-complete",
        "oap-smi-playback-state",
        "oap-smi-audio-cue",
        "oap-smi-human-stop",
        "oap-smi-background-stop",
    ]:
        assert required in collector

    assert "storesAudio:false" in collector
    assert "storesTranscript:false" in collector
    assert "storesUserAgent:false" in collector
    assert "localStorage" not in collector
    assert "sessionStorage" not in collector
    assert "sendBeacon" not in collector
    assert "WebSocket" not in collector

    assert "evidenceLayerSha256" in motion
    for layer in [
        "eyes",
        "head",
        "breathing",
        "mouth_visemes",
        "face",
        "hands",
        "upper_body",
    ]:
        assert layer in motion

    assert "androidEvidenceUrl" in template
    assert "smi_android_live_evidence.js" in template
    assert '@bp.post("/smi/android-live-evidence")' in views


def test_android_proof_stays_contextual_not_home_screen_noise():
    collector = COLLECTOR.read_text(encoding="utf-8")
    assert 'document.getElementById("attach-menu")' in collector
    assert 'id="android-proof-button"' not in TEMPLATE.read_text(encoding="utf-8")
    assert "Android Proof" in collector


def test_source_pixel_motion_canvas_is_visible_beneath_smi_controls():
    motion = MOTION.read_text(encoding="utf-8")
    css = Path("mission_control/static/smi_live_chat_dashboard.css").read_text(encoding="utf-8")
    assert "z-index:0" in motion
    assert "#smi-source-pixel-motion{z-index:0!important}" in css
    assert ".smi-shell>.workspace-grid{z-index:3!important}" in css
    assert ".smi-shell::after{z-index:2!important}" in css
    assert "z-index:-1" not in motion
