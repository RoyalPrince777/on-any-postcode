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
