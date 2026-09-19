from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "mission_control" / "templates" / "ollama_chat_base.html"
FINAL = ROOT / "mission_control" / "static" / "smi_chat_final.js"
CANON = ROOT / "mission_control" / "static" / "smi_canonical_controller.js"
CHARACTER = ROOT / "mission_control" / "static" / "smi_live_character.css"
DASHBOARD = ROOT / "mission_control" / "static" / "smi_sovereign_dashboard.css"
INTERACTION = ROOT / "mission_control" / "static" / "smi_interaction_layer.js"


def test_thinking_process_is_top_pinned_and_persistent():
    base = BASE.read_text(encoding="utf-8")
    thought = base.index('id="thinking"')
    character = base.index('id="smi-character"')
    messages = base.index('id="messages"')
    assert thought < character < messages
    assert "thinking.dataset.runActive='false'" in base
    assert "thinking.dataset.complete='true'" in base
    assert "thinking.classList.add('show')" in base
    assert "thinking.classList.remove('show')" not in base
    assert "thinkingLog.textContent='';thinking.dataset.runActive='true'" in base
    assert "Thinking Process · last completed run" in base


def test_live_smi_fullscreen_replaces_text_chat_but_keeps_controls():
    canon = CANON.read_text(encoding="utf-8")
    css = CHARACTER.read_text(encoding="utf-8")
    assert "smi-live-fullscreen" in canon
    assert "liveFullscreen:true" in canon
    assert "voiceFirstFullscreen:true" in canon
    assert "persistentThinkingProcess:true" in canon
    assert "Exit Live SMI" in canon
    assert "body.smi-live-fullscreen .messages{display:none!important}" in css
    assert "body.smi-live-fullscreen .composer textarea" in css
    assert "body.smi-live-fullscreen #plus-button" in css
    assert "body.smi-live-fullscreen #mic-button" in css
    assert "body.smi-live-fullscreen #stop-button" in css
    assert "body.smi-live-fullscreen .thinking{display:block!important" in css


def test_thought_process_stays_above_interaction_and_status_strips():
    final = FINAL.read_text(encoding="utf-8")
    interaction = INTERACTION.read_text(encoding="utf-8")
    assert "(q('#thinking')||head).insertAdjacentElement('afterend',ops)" in final
    assert '(document.getElementById("thinking") || chatHead).insertAdjacentElement("afterend", strip)' in interaction


def test_plus_tool_green_requires_current_session_runtime_receipt():
    final = FINAL.read_text(encoding="utf-8")
    assert "greenRequiresCurrentSessionReceipt:true" in final
    assert "functionHealthIsNotButtonProof:true" in final
    assert 'sessionStorage.setItem("oap_smi_button_proof:"+actionId' in final
    assert 'sessionStorage.getItem("oap_smi_button_proof:"+button.dataset.oapAction)' in final
    assert 'chip.textContent=proven?"Proven"' in final
    assert 'chip.classList.toggle("ready",proven)' in final
    assert 'chip.classList.toggle("ready",item.state==="green")' not in final
    assert "clickOnlyProof:false" in final


def test_legacy_action_handlers_are_gated_behind_single_control_surface():
    final = FINAL.read_text(encoding="utf-8")
    assert final.startswith("(()=>{")
    assert "window.OAP_SMI_CONTROL_SURFACE_V2_PENDING=true;" in final
    assert "if(!window.OAP_SMI_CONTROL_SURFACE_V2_PENDING)qa('[data-oap-action]')" in final
    assert "window.OAP_SMI_CONTROL_SURFACE_V2_PENDING=false;" in final


def test_default_connector_decoration_is_neutral_not_fake_green():
    base = BASE.read_text(encoding="utf-8")
    assert "<span>◇</span><span>Render</span>" in base
    assert "<span>◇</span><span>GitHub</span>" in base
    assert "<span>◇</span><span>Neon</span>" in base
    assert "<span>🟢</span><span>Neon</span>" not in base


def test_chat_and_dashboard_sizing_match_chat_first_layout():
    base = BASE.read_text(encoding="utf-8")
    dashboard = DASHBOARD.read_text(encoding="utf-8")
    assert "grid-template-columns:236px minmax(0,1fr)" in base
    assert "max-width:900px" in base
    assert "border-radius:26px" in base
    assert "min-height:31px;max-height:128px" in base
    assert "width:min(78vw,720px)!important" in dashboard
    assert "width:min(96vw,560px)!important" in dashboard
