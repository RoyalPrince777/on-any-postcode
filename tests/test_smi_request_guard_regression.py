from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GUARD = ROOT / "mission_control" / "static" / "smi_request_guard.js"
WRAPPER = ROOT / "mission_control" / "templates" / "ollama_chat.html"


def test_smi_request_guard_is_fail_closed_and_non_polling():
    guard = GUARD.read_text(encoding="utf-8")

    assert "let submitLocked=false" in guard
    assert "event.stopImmediatePropagation()" in guard
    assert "if(submitLocked||send?.disabled)return" in guard
    assert "form.addEventListener('submit',event=>" in guard
    assert "if(submitLocked){" in guard
    assert "event.preventDefault()" in guard
    assert "window.addEventListener('oap-smi-complete',release)" in guard
    assert "stop-button" in guard
    assert "setInterval(" not in guard
    assert "fetch(" not in guard
    assert "XMLHttpRequest" not in guard


def test_smi_request_guard_loads_once_after_chat_ui_layers():
    wrapper = WRAPPER.read_text(encoding="utf-8")

    assert wrapper.count("smi_request_guard.js") == 1
    assert wrapper.index("smi_chat_final.js") < wrapper.index("smi_request_guard.js")
    assert wrapper.index("smi_chat_compat.js") < wrapper.index("smi_request_guard.js")


def test_request_guard_captures_enter_before_existing_bubble_handlers():
    guard = GUARD.read_text(encoding="utf-8")

    enter_listener = "input.addEventListener('keydown',event=>{"
    assert enter_listener in guard
    start = guard.index(enter_listener)
    end = guard.index("},true);", start)
    capture_block = guard[start:end]
    assert "event.key!=='Enter'" in capture_block
    assert "event.preventDefault()" in capture_block
    assert "event.stopImmediatePropagation()" in capture_block
    assert "form.requestSubmit()" in capture_block
