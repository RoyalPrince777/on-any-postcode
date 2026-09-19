from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "mission_control" / "templates" / "ollama_chat_base.html"
WRAPPER = ROOT / "mission_control" / "templates" / "ollama_chat.html"
CONTROLLER = ROOT / "mission_control" / "static" / "smi_canonical_controller.js"
STATE = ROOT / "mission_control" / "static" / "smi_live_character_state.js"


def test_live_character_is_one_brain_surface():
    base = BASE.read_text(encoding="utf-8")
    assert base.count('id="smi-character"') == 1
    assert "One SMI Brain" in base
    assert 'id="live-character-toggle"' in base


def test_live_voice_privacy_boundary_is_explicit():
    base = BASE.read_text(encoding="utf-8")
    controller = CONTROLLER.read_text(encoding="utf-8")

    assert "audio-processing locality is not verified" in base
    assert "final recognised speech turns" in base
    assert "auto-sends" in base
    assert "browserSpeechLocalityVerified:false" in controller


def test_state_engine_loads_before_canonical_controller():
    wrapper = WRAPPER.read_text(encoding="utf-8")
    state_index = wrapper.index("smi_live_character_state.js")
    controller_index = wrapper.index("smi_canonical_controller.js")

    assert state_index < controller_index


def test_human_stop_is_epoch_guarded_and_sticky():
    controller = CONTROLLER.read_text(encoding="utf-8")
    state = STATE.read_text(encoding="utf-8")

    assert "oapApply('STOP')" in controller
    assert "tokenIsCurrent" in controller
    assert 'if(s.stopped)return next;' in state
    assert 'type==="RESUME_FROM_STOP"' in state


def test_all_mic_entry_uses_half_duplex_request_guard():
    controller = CONTROLLER.read_text(encoding="utf-8")

    assert "function oapRequestListening" in controller
    assert "oapStateApi.canListen(oapRuntime)" in controller
    assert "oapRequestListening('manual')" in controller
    assert "oapRequestListening('live')" in controller


def test_live_auto_send_requires_final_transcript():
    controller = CONTROLLER.read_text(encoding="utf-8")

    assert "result.isFinal" in controller
    assert "oapFinalTranscript" in controller
    assert "oapSubmit({fromLive:true})" in controller


def test_page_lifecycle_disables_live_capture():
    controller = CONTROLLER.read_text(encoding="utf-8")

    assert "pagehide" in controller
    assert "visibilitychange" in controller
    assert "Live SMI off while this page is hidden" in controller


def test_human_stop_control_remains_visible_for_active_voice_states():
    controller = CONTROLLER.read_text(encoding="utf-8")

    assert "function oapSyncHumanControls" in controller
    assert "oapRuntime.speaking" in controller
    assert "oapStop.classList.toggle('show'" in controller


def test_pause_suppresses_live_auto_submit():
    controller = CONTROLLER.read_text(encoding="utf-8")
    state = STATE.read_text(encoding="utf-8")

    assert "if(oapRuntime.listening)oapRecognitionToken=null" in controller
    assert "canAutoSubmitFinal" in controller
    assert "!s.paused" in state


def test_live_off_invalidates_state_before_browser_teardown():
    controller = CONTROLLER.read_text(encoding="utf-8")

    live_off = controller.index("function oapSetLive")
    live_off_end = controller.index("function oapRequestListening", live_off)
    block = controller[live_off:live_off_end]
    assert block.index("oapApply('LIVE_OFF')") < block.index("oapRecognition.stop()")
    assert "oapRecognitionToken=null" in block


def test_pagehide_invalidates_state_before_stopping_recognition():
    controller = CONTROLLER.read_text(encoding="utf-8")

    start = controller.index("window.addEventListener('pagehide'")
    block = controller[start:start + 500]
    assert block.index("oapApply('LIVE_OFF')") < block.index("oapRecognition.stop()")


def test_runtime_proof_ledger_is_redacted_and_memory_only():
    controller = CONTROLLER.read_text(encoding="utf-8")

    assert "window.OAP_SMI_LIVE_PROOF" in controller
    assert "storesAudio:false" in controller
    assert "storesTranscript:false" in controller
    assert "delete safe.transcript" in controller
    assert "delete safe.text" in controller
    assert "delete safe.audio" in controller
    assert "localStorage" not in controller
    assert "sessionStorage" not in controller
    assert "indexedDB" not in controller


def test_runtime_proof_records_authority_and_race_events():
    controller = CONTROLLER.read_text(encoding="utf-8")

    for marker in (
        "staleCallbackSuppressed",
        "halfDuplexDenied",
        "permissionDenied",
        "oapProof('stop'",
        "oapProof('pause'",
        "oapProof('resume'",
        "oapProof('liveOff'",
    ):
        assert marker in controller
