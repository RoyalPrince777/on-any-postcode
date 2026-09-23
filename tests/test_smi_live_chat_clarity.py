"""Guard the live SMI surface against persistent status/finished-work overlays."""
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_live_status_is_accessible_but_not_painted_over_character():
    css = (ROOT / "mission_control/static/smi_live_chat_dashboard.css").read_text(encoding="utf-8")
    assert ".status-row{position:absolute!important;width:1px!important;height:1px!important" in css
    assert "clip-path:inset(50%)!important" in css
    assert ".thinking[data-complete=\"true\"]{display:none!important}" in css


def test_primary_controls_and_original_artwork_are_preserved():
    css = (ROOT / "mission_control/static/smi_live_chat_dashboard.css").read_text(encoding="utf-8")
    assert "smi_live_chat_dashboard.jpg" in css
    for control in ("#plus-button", "#mic-button", "#thinking-level", "#send", "#stop-button"):
        assert control in css


def test_only_canonical_controller_emits_stream_completion():
    legacy = (ROOT / "mission_control/static/smi_chat_final.js").read_text(encoding="utf-8")
    controller = (ROOT / "mission_control/static/smi_canonical_controller.js").read_text(encoding="utf-8")
    assert "const nativeFetch=window.fetch.bind(window)" not in legacy
    assert "response.clone().text()" not in legacy
    assert "window.addEventListener('oap-smi-complete'" in legacy
    assert "window.dispatchEvent(new CustomEvent('oap-smi-complete',{detail:completeResult}))" in controller


def test_hrm_receipt_requires_a_unique_recorded_request():
    legacy = (ROOT / "mission_control/static/smi_chat_final.js").read_text(encoding="utf-8")
    assert "const oapRenderedReceiptIds=new Set()" in legacy
    assert "typeof r.request_id!=='string'" in legacy
    assert "typeof r.conversation_id!=='string'" in legacy
    assert "if(oapRenderedReceiptIds.has(receiptKey))return" in legacy
    assert "oapRenderedReceiptIds.add(receiptKey)" in legacy
    assert "oapRenderedReceiptIds.size>128" in legacy
    assert "Shown only after the governed response completed" in legacy


def test_cancelled_stream_cannot_complete_or_clear_newer_request():
    controller = (ROOT / "mission_control/static/smi_canonical_controller.js").read_text(encoding="utf-8")
    assert "const requestAbort=oapAbort" in controller
    assert "signal:requestAbort.signal" in controller
    assert controller.count("if(requestAbort.signal.aborted||oapAbort!==requestAbort)return") >= 2
    assert "if(oapAbort===requestAbort){if(oapWorkStarted)oapEndWork()" in controller
    assert "window.dispatchEvent(new CustomEvent('oap-smi-complete',{detail:completeResult}))" in controller


def test_stopped_state_requires_a_valid_explicit_command_before_resume():
    controller = (ROOT / "mission_control/static/smi_canonical_controller.js").read_text(encoding="utf-8")
    submit = controller[controller.index("async function oapSubmit("):controller.index("oapInput.addEventListener('keydown'")]
    assert "if(oapRuntime?.stopped&&fromLive)return;" in submit
    assert submit.index("if(oapLocked||oapSend.disabled)return") < submit.index("if(oapRuntime?.stopped)oapApply('RESUME_FROM_STOP')")
    assert submit.index("if(!text&&!hasImage&&!hasAttachment)return;") < submit.index("if(oapRuntime?.stopped)oapApply('RESUME_FROM_STOP')")


def test_recovery_preserves_exact_approved_character_and_fail_closed_rig():
    source = ROOT / "static/oap/smi_live_chat_dashboard.jpg"
    assert hashlib.sha256(source.read_bytes()).hexdigest() == (
        "f9503174f6f18b815f1c73e24faff3b4966c2e1fbae8d20a8d2bcc22e4a84a4b"
    )
    rig = (ROOT / "mission_control/static/smi_exact_character_rig.js").read_text(encoding="utf-8")
    assert 'const LOCK="design_only_no_approved_layered_rig"' in rig
    assert "function frame(){return null;}" in rig
    assert "function activate(){rejectedEvents+=1;return freezeSnapshot();}" in rig


def test_stale_microphone_callbacks_cannot_mutate_mobile_controls():
    controller = (ROOT / "mission_control/static/smi_canonical_controller.js").read_text(encoding="utf-8")
    for ending in ("recognition-end", "recognition-error"):
        start = controller.index("const expected=oapRecognitionToken;if(!oapStateApi.tokenIsCurrent", controller.index("oapRecognition.onend=()=>" if ending == "recognition-end" else "oapRecognition.onerror=event=>"))
        callback = controller[start:controller.index("oapApply('LISTEN_END')", start)]
        assert callback.index("staleCallbackSuppressed") < callback.index("oapStopListenTimer()")
        assert callback.index("staleCallbackSuppressed") < callback.index("oapMic.classList.remove('active')")


def test_camera_and_screen_cannot_restore_media_after_stop():
    source = (ROOT / "mission_control/static/smi_canonical_controller.js").read_text(encoding="utf-8")
    capture = source[source.index("async function oapCaptureFrame("):source.index("function oapAddCaptureOptions()")]
    assert "async function oapCaptureFrame(stream,label,expectedEpoch)" in capture
    assert capture.count("oapRuntime?.stopped||!oapStateApi.tokenIsCurrent(oapRuntime,expectedEpoch)") >= 3
    assert "stream.getTracks().forEach(track=>track.stop())" in capture
    assert "await oapCaptureFrame(stream,'Camera',captureEpoch)" in capture
    assert "await oapCaptureFrame(stream,'Screen',captureEpoch)" in capture
    assert capture.count("if(oapRuntime?.stopped){oapSetStatus('Stopped by Human Authority');return;}") >= 2


def test_stale_capture_permission_outcomes_do_not_overwrite_stop():
    source = (ROOT / "mission_control/static/smi_canonical_controller.js").read_text(encoding="utf-8")
    capture = source[source.index("async function oapCamera()"):source.index("function oapAddCaptureOptions()")]
    guard = "if(oapRuntime?.stopped||!oapStateApi.tokenIsCurrent(oapRuntime,captureEpoch))return;"
    assert capture.count(guard) >= 2
    assert "stream.getTracks().forEach(track=>track.stop());return;}oapSetStatus('Sharing" in capture
    assert capture.index("stream.getTracks().forEach(track=>track.stop());return;}oapSetStatus('Sharing") < capture.index("await oapCaptureFrame(stream,'Screen',captureEpoch)")


def test_human_stop_closes_active_camera_and_screen_tracks_synchronously():
    source = (ROOT / "mission_control/static/smi_canonical_controller.js").read_text(encoding="utf-8")
    assert "const oapActiveCaptureStreams=new Set();" in source
    stop = source[source.index("function oapStopAll(){"):source.index("function oapTogglePause(){")]
    assert "for(const stream of oapActiveCaptureStreams)" in stop
    assert "stream.getTracks().forEach(track=>track.stop())" in stop
    assert stop.index("oapActiveCaptureStreams.clear()") < stop.index("oapApply('STOP')")
    capture = source[source.index("async function oapCaptureFrame("):source.index("function oapAddCaptureOptions()")]
    assert "oapActiveCaptureStreams.delete(stream)" in capture
    assert "oapActiveCaptureStreams.add(stream);await oapCaptureFrame(stream,'Camera',captureEpoch)" in capture
    assert "oapActiveCaptureStreams.add(stream);await oapCaptureFrame(stream,'Screen',captureEpoch)" in capture
