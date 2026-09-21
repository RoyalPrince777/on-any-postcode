from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WRAPPER = ROOT / "mission_control" / "templates" / "ollama_chat.html"
CONTROLLER = ROOT / "mission_control" / "static" / "smi_canonical_controller.js"


def test_canonical_controller_is_the_only_loaded_core_request_owner():
    wrapper = WRAPPER.read_text(encoding="utf-8")
    assert wrapper.count("smi_canonical_controller.js") == 1
    assert "smi_request_guard.js" not in wrapper
    assert wrapper.index("smi_chat_final.js") < wrapper.index("smi_canonical_controller.js")
    assert wrapper.index("smi_chat_compat.js") < wrapper.index("smi_canonical_controller.js")


def test_canonical_controller_owns_one_submit_path_fail_closed():
    text = CONTROLLER.read_text(encoding="utf-8")
    assert "let oapLocked=false" in text
    assert "if(oapLocked||oapSend.disabled)return" in text
    assert "oapInput.addEventListener('keydown'" in text
    assert "oapForm.addEventListener('submit'" in text
    assert text.count("event.stopImmediatePropagation()") >= 6
    assert "oapSubmit();" in text
    assert "add(userLabel,'user')" in text
    assert "oapInput.dispatchEvent(new Event('input',{bubbles:true}))" in text
    assert "window.OAP_SMI_CANONICAL" in text
    assert "singleSubmitOwner:true" in text
    assert "composerOwner:true" in text


def test_canonical_controller_owns_plus_drawer_and_outside_close():
    text = CONTROLLER.read_text(encoding="utf-8")
    assert "const oapPlus=document.getElementById('plus-button')" in text
    assert "function oapToggleAttach()" in text
    assert "oapAttachMenu.classList.toggle('show',open)" in text
    assert "oapPlus.setAttribute('aria-expanded',String(open))" in text
    assert "oapPlus.addEventListener('click'" in text
    assert "event.target.closest('.attach-wrap')" in text
    assert "plusOwner:true" in text


def test_canonical_controller_owns_pause_resume_and_stop():
    text = CONTROLLER.read_text(encoding="utf-8")
    assert "const oapPause=document.getElementById('pause-button')" in text
    assert "function oapTogglePause()" in text
    assert "while(oapPaused&&!responseStopped)" in text
    assert "speechSynthesis.pause()" in text
    assert "speechSynthesis.resume()" in text
    assert "oapAbort.abort()" in text
    assert "pauseOwner:true" in text
    assert "stopOwner:true" in text


def test_canonical_controller_forwards_thinking_and_studio_modes():
    text = CONTROLLER.read_text(encoding="utf-8")
    assert "const oapThinkingLevel=document.getElementById('thinking-level')" in text
    assert "selectedThinkingLevel=oapThinkingLevel?.value||'auto'" in text
    assert "selectedStudioMode=" in text
    assert "thinking_level:selectedThinkingLevel" in text
    assert "studio_mode:selectedStudioMode" in text
    assert "thinkingModeOwner:true" in text
    assert "studioModeOwner:true" in text


def test_canonical_controller_owns_worked_for_timing_and_safe_progress():
    text = CONTROLLER.read_text(encoding="utf-8")
    assert "const oapThinkingElapsed=document.getElementById('thinking-elapsed')" in text
    assert "function oapBeginWork()" in text
    assert "function oapEndWork()" in text
    assert "Worked for ${seconds.toFixed(1)}s" in text
    assert "showStage('Understand')" in text
    assert "showStage('Context')" in text
    assert "parsed.event==='stage'" in text
    assert "timingOwner:true" in text


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
    assert "screen-capture-button" in text
    assert "screen.id='screen-button'" not in text
    assert "studioDuplicate:false" in text


def test_canonical_controller_preserves_governed_backend_contract():
    text = CONTROLLER.read_text(encoding="utf-8")
    assert "streamUrl" in text
    assert "'X-OAP-CSRF':csrfToken" in text
    assert "credentials:'same-origin'" in text
    assert "event: complete" not in text
    assert "oap-smi-complete" in text
    assert "Human Authority" in text


def test_only_canonical_acceptance_emits_live_chat_completion():
    canonical = CONTROLLER.read_text(encoding="utf-8")
    enhancement = (ROOT / "mission_control" / "static" / "smi_chat_final.js").read_text(encoding="utf-8")
    assert canonical.count("new CustomEvent('oap-smi-complete'") == 1
    assert "if(streamError)throw streamError;if(!completeResult)throw" in canonical
    assert canonical.index("if(streamError)throw streamError;if(!completeResult)throw") < canonical.index("new CustomEvent('oap-smi-complete'")
    assert "response.clone().text()" not in enhancement
    assert "new CustomEvent('oap-smi-complete'" not in enhancement
    assert "window.addEventListener('oap-smi-complete'" in enhancement


def test_stop_cannot_emit_canonical_completion_or_duplicate_receipt_card():
    canonical = CONTROLLER.read_text(encoding="utf-8")
    enhancement = (ROOT / "mission_control" / "static" / "smi_chat_final.js").read_text(encoding="utf-8")
    guard = "if(responseStopped||oapAbort.signal.aborted)throw new DOMException"
    assert guard in canonical
    assert canonical.index(guard) < canonical.index("new CustomEvent('oap-smi-complete'")
    assert "const seenReceiptIds=new Set()" in enhancement
    assert "if(!receiptId||seenReceiptIds.has(receiptId))return" in enhancement
