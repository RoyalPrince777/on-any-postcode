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


def test_real_composer_is_aligned_to_painted_art_not_duplicated():
    assert 'const composer=document.getElementById("chat-form")' in JS
    assert 'aligned.append(composer)' in JS
    assert 'document.body.append(aligned)' in JS
    assert 'picture.width=wallpaper.naturalWidth' in JS
    assert 'picture.height=wallpaper.naturalHeight' in JS
    assert 'const scale=Math.min(width/picture.width,height/picture.height)' in JS
    assert 'observer.observe(scene)' in JS
    assert 'id="chat-form"' in BASE
    assert BASE.count('id="chat-form"') == 1
    assert 'smi-image-control-surface #message' in CSS
    assert 'smi-image-control-surface #plus-button' in CSS
    assert 'smi-image-control-surface #mic-button' in CSS
    assert 'smi-image-control-surface #thinking-level' in CSS
    assert 'smi-image-control-surface #send' in CSS
    assert 'pointer-events:auto!important' in CSS


def test_stop_is_visible_outside_picture_and_mobile_controls_are_touch_sized():
    assert 'for(const id of ["code-button","speaker-button","pause-button","stop-button"])' in JS
    assert 'panel.querySelector(".smi-command-top").append(safetyTools)' in JS
    assert 'smi-command-safety-tools #stop-button' in CSS
    assert 'display:grid!important;place-items:center!important;' in CSS
    assert 'width:44px!important;height:44px!important;min-width:44px!important' in CSS
    assert 'height:44px!important' in CSS
    assert 'font-size:16px!important' in CSS
    assert 'bottom:calc(126px + env(safe-area-inset-bottom))' in CSS
    assert 'pointer-events:none' in CSS
    assert 'pointer-events:auto' in CSS


def test_no_artwork_gives_visible_fail_closed_real_input():
    # Start in visible-fallback mode until the real first-party PNG finishes loading.
    assert JS.index('document.body.classList.add("smi-art-error")') < JS.index("wallpaper.onload=()=>{")
    assert 'panel.classList.add("smi-art-error")' in JS
    assert 'panel.classList.remove("smi-art-error")' in JS
    assert 'no substitute character shown' in JS
    assert 'body.smi-command-open.smi-art-error' in CSS


def test_baked_status_is_covered_by_real_evidence_not_fake_green():
    assert 'aligned.append(dashboard)' in JS
    assert 'evidence.append(dashboard)' not in JS
    assert 'setRoom(roomStats.get("runtime"),health?.ready===true' in JS
    assert 'setRoom(roomGates.get("founder"),false' in JS
    assert '.smi-image-control-surface>.smi-room-status' in CSS
    assert 'background:#020c1ef9!important' in CSS


def test_android_keyboard_and_bfcache_restore_the_same_canonical_composer():
    assert 'window.visualViewport.addEventListener("resize",alignApprovedBar)' in JS
    assert 'window.visualViewport.addEventListener("scroll",alignApprovedBar)' in JS
    assert 'window.addEventListener("pageshow",event=>' in JS
    assert 'if(event.persisted)' in JS
    assert 'if(sceneObserver)sceneObserver.observe(scene)' in JS
    assert 'if(sceneObserver)sceneObserver.disconnect()' in JS
    assert 'setOpen(true);' in JS
    assert 'alignApprovedBar();' in JS
    assert 'document.body.append(aligned)' in JS
    assert BASE.count('id="chat-form"') == 1


def test_scene_only_hitboxes_and_chat_tab_recovery():
    # Absolute picture hitboxes must never float over hidden Anatomy/Evidence.
    assert 'let active=false;' in JS
    assert 'let active=false,request=null,roomRequest=null;' not in JS
    assert 'panel.dataset.mobileView!=="scene"||!width||!height' in JS
    assert 'aligned.style.visibility="hidden"' in JS
    assert 'aligned.setAttribute("inert","")' in JS
    assert 'aligned.style.visibility="visible"' in JS
    assert 'aligned.removeAttribute("inert")' in JS
    assert 'panel.dataset.mobileView=tab.dataset.view;' in JS
    assert 'panel.dataset.mobileView="scene";' in JS
    assert 'alignApprovedBar();' in JS
    assert 'button.dataset.view==="scene"' in JS
