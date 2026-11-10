from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_smi_noise_strip_assets_are_loaded_last():
    template = (ROOT / "mission_control" / "templates" / "ollama_chat.html").read_text()
    assert "smi_noise_strip.css" in template
    assert "smi_noise_strip.js" in template
    assert template.index("smi_noise_strip.css") > template.index("smi_live_chat_dashboard.css")
    assert template.index("smi_noise_strip.js") > template.index("smi_command_centre.js")


def test_smi_noise_strip_preserves_core_controls_and_functions():
    base = (ROOT / "mission_control" / "templates" / "ollama_chat_base.html").read_text()
    js = (ROOT / "mission_control" / "static" / "smi_noise_strip.js").read_text()
    for control_id in ("plus-button", "mic-button", "pause-button", "stop-button", "send"):
        assert f'id="{control_id}"' in base
        assert control_id in js
    assert "addEventListener('keydown'" not in js
    assert "canonical controller" in js
    assert "upgradeOnly:true" in js


def test_smi_noise_strip_is_visual_not_route_removal():
    css = (ROOT / "mission_control" / "static" / "smi_noise_strip.css").read_text()
    template = (ROOT / "mission_control" / "templates" / "ollama_chat.html").read_text()
    assert "display:none" in css
    assert "studioGenerateUrl" in template
    assert "studioBuildPreviewCreateUrl" in template
    assert "warRoomUrl" in template
    assert "greenGateUrl" in template


def test_live_control_is_forced_visible_outside_dashboard_layout():
    js = (ROOT / "mission_control" / "static" / "smi_noise_strip.js").read_text()
    assert "document.getElementById('live-character-toggle')" in js
    assert "document.body.appendChild(liveToggle)" in js
    assert "liveToggle.style.setProperty('display','grid','important')" in js
    assert "liveToggle.style.setProperty('visibility','visible','important')" in js
    assert "liveToggle.style.setProperty('opacity','1','important')" in js
    assert "liveToggle.style.setProperty('pointer-events','auto','important')" in js
    assert "liveToggle.style.setProperty('z-index','1200','important')" in js


def test_legacy_dashboard_chrome_is_suppressed_before_first_paint():
    base = (ROOT / "mission_control" / "templates" / "ollama_chat_base.html").read_text()
    assert 'id="smi-first-paint-guard"' in base
    assert '<body class="mc-workspace-body smi-noise-strip smi-booting">' in base
    assert '<nav class="navs" hidden inert aria-hidden="true">' in base
    assert '<section class="smi-hero" hidden inert aria-hidden="true">' in base
    assert '<header class="chat-head" hidden aria-hidden="true">' in base


def test_failed_request_restores_composer_for_retry():
    canonical = (ROOT / "mission_control" / "static" / "smi_canonical_controller.js").read_text()
    assert "if(!oapInput.value.trim()&&text)oapInput.value=text" in canonical
    assert "Your request is preserved for retry." in canonical
    assert "Inference unavailable · request preserved · retry when backend is ready" in canonical
    assert "oapInput.focus()" in canonical


def test_live_fullscreen_keeps_minimum_text_fallback_controls_visible():
    css = (ROOT / "mission_control" / "static" / "smi_noise_strip.css").read_text(encoding="utf-8")
    assert "Canonical Live SMI input law" in css
    assert "body.smi-noise-strip.smi-live-fullscreen .composer textarea" in css
    assert "display:block!important" in css
    assert "body.smi-noise-strip.smi-live-fullscreen #send" in css
    assert "body.smi-noise-strip.smi-live-fullscreen #mic-button" in css
    assert "body.smi-noise-strip.smi-live-fullscreen #plus-button" in css
    assert "body.smi-noise-strip.smi-live-fullscreen #thinking-level" in css


def test_live_fullscreen_surfaces_recovery_message():
    canonical = (ROOT / "mission_control" / "static" / "smi_canonical_controller.js").read_text()
    assert "if(oapRuntime?.live)oapShowLiveReply('Inference unavailable · your request is preserved for retry.')" in canonical
    assert "Your request is preserved for retry." in canonical


def test_canonical_ui_ownership_is_not_split_across_surface_styles():
    noise = (ROOT / "mission_control" / "static" / "smi_noise_strip.css").read_text(encoding="utf-8")
    live = (ROOT / "mission_control" / "static" / "smi_live_character.css").read_text(encoding="utf-8")
    assert "Canonical UI ownership: Live fullscreen layout." in noise
    assert "body.smi-noise-strip.smi-live-fullscreen .workspace-grid" in noise
    assert "body.smi-live-fullscreen .workspace-grid" not in live
    assert "body.smi-live-fullscreen .composer" not in live
    assert "body.smi-live-fullscreen .thinking" not in live

def test_noise_strip_does_not_restyle_dedicated_dashboard_or_command_surfaces():
    noise = (ROOT / "mission_control" / "static" / "smi_noise_strip.css").read_text(encoding="utf-8")
    assert "smi-command-layout{" not in noise
    assert "smi-dashboard-shell{" not in noise
    assert "smi-summary-card{" not in noise

def test_first_paint_guard_only_prevents_flash_not_persistent_layout():
    base = (ROOT / "mission_control" / "templates" / "ollama_chat_base.html").read_text(encoding="utf-8")
    guard = base.split('id="smi-first-paint-guard"', 1)[1].split("</style>", 1)[0]
    assert "smi-booting" in guard
    assert ".composer{position:fixed" not in guard
    assert ".workspace-grid{grid-template-columns" not in guard

def test_reference_command_room_uses_real_evidence_and_mobile_drawer():
    css = (ROOT / "mission_control" / "static" / "smi_noise_strip.css").read_text(encoding="utf-8")
    js = (ROOT / "mission_control" / "static" / "smi_noise_strip.js").read_text(encoding="utf-8")
    assert "SMI visual reference: gold command-room frame" in css
    assert "@media(max-width:760px)" in css
    assert "smi-reference-nav-open" in css
    assert "smi-reference-right" in css
    assert "smi-reference-layout" in js
    assert "document.getElementById('smi-reference-top')" in js
    assert "window.OAP_SMI_UI?.healthUrl" in js
    assert "value===true?'Passed'" in js
    assert "Unknown · No Green inferred" in js
    assert "fetch(url,{credentials:'same-origin',cache:'no-store'})" in js
    assert "document.addEventListener('keydown'" not in js

def test_reference_mobile_evidence_drawer_does_not_cover_live_smi():
    css = (ROOT / "mission_control" / "static" / "smi_noise_strip.css").read_text(encoding="utf-8")
    js = (ROOT / "mission_control" / "static" / "smi_noise_strip.js").read_text(encoding="utf-8")
    assert "smi-reference-evidence-toggle" in css
    assert "smi-reference-evidence-open" in css
    assert "smi-reference-evidence-toggle" in js
    assert "smi-reference-evidence-open" in js
    assert "smi-reference-layout.smi-live-fullscreen .smi-reference-top" in css
    assert "smi-reference-layout.smi-live-fullscreen .smi-reference-side" in css
    assert "closeEvidence();" in js
    assert "window.OAP_SMI_UI?.healthUrl" in js
    assert "Unknown · No Green inferred" in js


def test_smi_evidence_health_refresh_is_bounded_and_fail_closed():
    js = (ROOT / "mission_control" / "static" / "smi_noise_strip.js").read_text(encoding="utf-8")
    assert "if(checkingEvidence)return" in js
    assert "refresh.disabled=true" in js
    assert "const controller=new AbortController()" in js
    assert "setTimeout(()=>controller.abort(),8000)" in js
    assert "signal:controller.signal" in js
    assert "clearTimeout(timeout)" in js
    assert "Unknown · No Green inferred" in js
    assert "refresh.disabled=false" in js


def test_reference_mobile_closed_drawers_are_not_focusable():
    js = (ROOT / "mission_control" / "static" / "smi_noise_strip.js").read_text(encoding="utf-8")
    assert "const mobileLayout=window.matchMedia('(max-width:760px)')" in js
    assert "left.inert=!navOpen" in js
    assert "right.inert=!evidenceOpen" in js
    assert "left.setAttribute('aria-hidden',String(!navOpen))" in js
    assert "right.setAttribute('aria-hidden',String(!evidenceOpen))" in js
    assert "mobileLayout.addEventListener('change',syncDrawerAccess)" in js
    assert "syncDrawerAccess();" in js
