"""Guard the live SMI surface against persistent status/finished-work overlays."""
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
