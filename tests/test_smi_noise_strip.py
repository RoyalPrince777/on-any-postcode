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
    assert '<body class="mc-workspace-body smi-noise-strip">' in base
    assert "smi-booting" not in base
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


def test_primary_controls_remain_human_readable_not_emoji_only():
    css = (ROOT / "mission_control" / "static" / "smi_noise_strip.css").read_text(encoding="utf-8")
    base = (ROOT / "mission_control" / "templates" / "ollama_chat_base.html").read_text(encoding="utf-8")
    for label in ("Tools", "Voice", "Pause", "Stop", "Send"):
        assert f">{label}<" in base or f">{label}</span>" in base
    assert 'class="control-label">Tools</span>' in base
    assert 'class="control-label">Voice</span>' in base
    assert 'class="control-label">Pause</span>' in base
    assert 'class="control-label">Stop</span>' in base
    assert ".control-label{" in css
    assert 'content:none!important' in css
    assert ".send-label{display:inline!important" in css


def test_final_smi_shell_does_not_wait_for_dom_ready_to_become_visible():
    base = (ROOT / "mission_control" / "templates" / "ollama_chat_base.html").read_text(encoding="utf-8")
    js = (ROOT / "mission_control" / "static" / "smi_noise_strip.js").read_text(encoding="utf-8")
    assert 'class="mc-workspace-body smi-noise-strip"' in base
    assert "smi-booting" not in base
    assert "classList.remove('smi-booting')" not in js


def test_first_paint_guard_is_inside_head_before_body():
    base = (ROOT / "mission_control" / "templates" / "ollama_chat_base.html").read_text(encoding="utf-8")
    guard = base.index('id="smi-first-paint-guard"')
    head_close = base.index("</head>")
    body = base.index("<body")
    assert guard < head_close < body


def test_war_room_uses_direct_configured_route_not_hidden_tool_proxy():
    command = (ROOT / "mission_control" / "static" / "smi_command_centre.js").read_text(encoding="utf-8")
    assert "const openWarRoom=()=>{" in command
    assert "cfg.warRoomUrl" in command
    assert "window.location.assign(target)" in command
    assert 'if(target==="war-room"){openWarRoom();return;}' in command
    assert 'if(action==="war-room")' in command
    assert '#attach-menu [data-oap-action="war-room"]' not in command


def test_voice_and_pause_state_changes_keep_readable_labels():
    canonical = (ROOT / "mission_control" / "static" / "smi_canonical_controller.js").read_text(encoding="utf-8")
    assert 'class="control-label">Resume</span>' in canonical
    assert 'class="control-label">Pause</span>' in canonical
    assert 'class="control-label">Stop voice</span>' in canonical
    assert 'class="control-label">Voice</span>' in canonical


def test_quiet_home_shows_only_primary_composer_controls():
    css = (ROOT / "mission_control" / "static" / "smi_noise_strip.css").read_text(encoding="utf-8")
    base = (ROOT / "mission_control" / "templates" / "ollama_chat_base.html").read_text(encoding="utf-8")
    canonical = (ROOT / "mission_control" / "static" / "smi_canonical_controller.js").read_text(encoding="utf-8")
    assert "Final noise strip: one quiet front-door composer." in css
    assert "body.smi-noise-strip #speaker-button{\n  display:none!important;" in css
    assert 'id="voice-reply-menu-button"' in base
    assert "oapVoiceReplyMenu" in canonical
    assert "oapSpeaker?.click()" in canonical
    for label in ("Tools", "Voice", "Send"):
        assert label in base


def test_home_restores_system_context_without_dashboard_wall():
    command = (ROOT / "mission_control" / "static" / "smi_command_centre.js").read_text(encoding="utf-8")
    css = (ROOT / "mission_control" / "static" / "smi_noise_strip.css").read_text(encoding="utf-8")
    assert 'className="smi-home-intelligence"' in command
    for label in ("SMI System", "Matrix", "War Room"):
        assert label in command
    assert 'homeSystem.addEventListener("click",()=>setOpen(true))' in command
    assert 'homeMatrix.addEventListener("click",()=>window.location.assign("/mission/war-room/routes"))' in command
    assert 'homeWar.addEventListener("click",()=>openWarRoom())' in command
    assert "Home intelligence rail: restore system context without restoring dashboard noise." in css
    assert "body.smi-noise-strip.smi-command-open .smi-home-intelligence" in css
    assert "body.smi-noise-strip.smi-live-fullscreen .smi-home-intelligence" in css


def test_unified_system_intelligence_reuses_canonical_evidence():
    command = (ROOT / "mission_control" / "static" / "smi_command_centre.js").read_text(encoding="utf-8")
    css = (ROOT / "mission_control" / "static" / "smi_noise_strip.css").read_text(encoding="utf-8")
    assert 'className="smi-unified-intelligence"' in command
    for key in ("mission", "matrix", "guardian", "hrm", "signals", "gate"):
        assert f'["{key}"' in command or f'"{key}"' in command
    for url in ("cfg.healthUrl", "cfg.functionHealthUrl", "cfg.signalsUrl",
                "cfg.greenGateUrl", "cfg.routesUrl", "cfg.hrmUrl"):
        assert url in command
    assert "No verified active mission feed · do not infer one" in command
    assert "Route evidence reachable · Matrix world-state not certified" in command
    assert "HRM source reached · durable receipt not certified" in command
    assert 'setUnified("gate",gate?.green===true' in command
    assert 'setUnified("signals",signalProven' in command
    assert 'panel.dataset.mobileView="evidence"' in command
    assert "smi-unified-grid" in css
    assert "grid-template-columns:1fr!important" in css
    assert 'className="smi-system-detail"' in command
    assert 'evidenceDetail.append(evidenceSummary,dashboard)' in command
