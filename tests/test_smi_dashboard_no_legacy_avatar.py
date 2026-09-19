"""The exact approved dashboard is SMI's one persistent visual front door.

No retired avatar flash, duplicate chat controller, hidden Plus or fake proof.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = (ROOT / "mission_control/templates/ollama_chat_base.html").read_text()
WRAPPER = (ROOT / "mission_control/templates/ollama_chat.html").read_text()
JS = (ROOT / "mission_control/static/smi_command_centre.js").read_text()
CSS = (ROOT / "mission_control/static/smi_command_centre.css").read_text()
CONTROLLER = (ROOT / "mission_control/static/smi_canonical_controller.js").read_text()


def test_retired_character_has_no_visible_markup_or_fallback_flash():
    assert 'id="smi-character"' in BASE  # hidden single state owner survives
    assert 'hidden style="display:none!important"' in BASE
    assert 'smi-person smi-cybernetic' not in BASE
    assert '<div class="smi-character-stage">' not in BASE
    assert "marker.parentNode.insertBefore(character,marker)" not in JS
    assert "stage.append(character)" not in JS
    assert ".smi-command-scene .smi-person" in CSS
    assert 'panel.classList.remove("smi-room-art-loaded")' in JS
    assert "no substitute character shown" in JS


def test_whole_approved_dashboard_has_no_crop_and_controls_are_real():
    assert "oap/smi_global_intelligence_command_centre.png" in WRAPPER
    assert "wallpaper.src=cfg.approvedWallpaperUrl" in JS
    assert 'panel.classList.add("smi-room-art-loaded")' in JS
    assert 'background-size:contain!important' in CSS
    assert '.smi-command-layout{' in CSS
    assert 'grid-template-columns:minmax(0,1fr)!important' in CSS
    assert 'getElementById("live-character-toggle")' in JS
    assert 'getElementById("messages")' in JS
    assert 'id="plus-button"' in BASE
    assert 'id="mic-button"' in BASE
    assert 'id="stop-button"' in BASE
    assert "oap-smi-character-state" in JS


def test_chat_and_send_stay_within_dashboard_and_use_one_controller():
    assert 'event.target?.id==="chat-form"&&active)setChatVisible(true)' in JS
    assert 'event.target?.id==="message"&&event.key==="Enter"' in JS
    assert 'setChatVisible(true);' in JS
    assert 'if(detail.live&&active)setOpen(false)' not in JS
    assert "setOpen(true);" in JS
    assert "smi-command-chat-visible" in JS
    assert '.chatbox>.messages' in CSS
    assert '.composer' in CSS
    assert "canonical.click()" in JS
    assert "function oapRenderCharacter()" in CONTROLLER


def test_live_voice_does_not_hijack_the_artwork_and_respects_reduced_motion():
    assert 'body.smi-live-fullscreen.smi-command-open .smi-command-centre' in CSS
    assert 'body.smi-live-fullscreen.smi-command-open #live-character-toggle' in CSS
    assert 'body.smi-live-fullscreen.smi-command-open .composer textarea' in CSS
    assert 'body.smi-live-fullscreen.smi-command-open #send' in CSS
    assert 'body.smi-live-fullscreen.smi-command-open .composer-left>*' in CSS
    assert 'prefers-reduced-motion:reduce' in CSS
    assert 'setRoom(roomGates.get("founder"),false' in JS
