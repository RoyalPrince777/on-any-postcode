"""Actual completed Live SMI replies appear beside the unchanged approved portrait."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "mission_control/templates/ollama_chat_base.html"
CONTROLLER = ROOT / "mission_control/static/smi_canonical_controller.js"
CSS = ROOT / "mission_control/static/smi_approved_presence.css"


def test_one_accessible_live_reply_caption_in_original_character():
    page = BASE.read_text(encoding="utf-8")
    assert page.count('id="smi-live-reply-caption"') == 1
    assert 'aria-label="Latest SMI reply" hidden' in page
    assert 'class="smi-approved-portrait"' in page


def test_only_real_completed_reply_is_displayed_without_html_injection():
    source = CONTROLLER.read_text(encoding="utf-8")
    assert "oapLiveCaption.textContent=visible?String(text):''" in source
    assert "oapShowLiveReply(completeResult.response);oapSpeak(completeResult.response)" in source
    assert "oapRuntime?.live&&!oapRuntime.stopped" in source
    assert "oapLiveCaption.innerHTML" not in source
    assert "oap-smi-playback-state" in source


def test_stop_live_off_and_new_turn_clear_caption():
    source = CONTROLLER.read_text(encoding="utf-8")
    assert "oapApply('STOP');oapShowLiveReply('')" in source
    assert "oapApply('LIVE_OFF');oapShowLiveReply('')" in source
    assert "oapLocked=true;responseStopped=false;oapPaused=false;oapShowLiveReply('')" in source
    assert "if(seq!==oapSpeechSeq||!oapStateApi.tokenIsCurrent(oapRuntime,expected))" in source


def test_caption_is_fullscreen_only_and_never_distorts_artwork():
    css = CSS.read_text(encoding="utf-8")
    assert ".smi-live-reply-caption{display:none}" in css
    assert "body.smi-live-fullscreen .smi-live-reply-caption:not([hidden])" in css
    assert ".smi-approved-portrait" in css
    assert "mouthScaleY" not in css
