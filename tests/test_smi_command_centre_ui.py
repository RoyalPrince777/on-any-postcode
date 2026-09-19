"""Source-level regression contract for the additive SMI Command Centre."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "mission_control" / "static"
TEMPLATE = ROOT / "mission_control" / "templates" / "ollama_chat.html"


class CommandCentreUITest(unittest.TestCase):
    def test_loaded_after_canonical_components(self):
        page = TEMPLATE.read_text(encoding="utf-8")
        self.assertIn("smi_command_centre.css", page)
        self.assertIn("smi_command_centre.js", page)
        self.assertLess(page.index("smi_canonical_controller.js"), page.index("smi_command_centre.js"))
        self.assertLess(page.index("smi_live_character.css"), page.index("smi_command_centre.css"))

    def test_existing_character_and_controls_are_reused(self):
        source = (STATIC / "smi_command_centre.js").read_text(encoding="utf-8")
        self.assertIn('getElementById("smi-character")', source)
        self.assertIn('getElementById("messages")', source)
        self.assertIn("marker.parentNode.insertBefore(character,marker)", source)
        self.assertIn('oap-smi-character-state', source)
        self.assertNotIn("All Systems Operational", source)

    def test_health_truth_is_fail_closed(self):
        source = (STATIC / "smi_command_centre.js").read_text(encoding="utf-8")
        self.assertIn("data.checks[key]===true", source)
        self.assertIn('state.textContent=proven?"Proven by check":"Not proven"', source)
        self.assertIn('state.textContent="Unavailable"', source)
        self.assertIn('credentials:"same-origin"', source)

    def test_tools_tab_does_not_close_its_own_drawer(self):
        controller = (STATIC / "smi_canonical_controller.js").read_text(
            encoding="utf-8"
        )
        interaction = (STATIC / "smi_interaction_layer.js").read_text(
            encoding="utf-8"
        )
        self.assertIn("!event.target.closest('#tools-mode-button')", controller)
        self.assertIn('      plus.click();', interaction)
        self.assertNotIn(
            'if (!attachMenu.classList.contains("show")) plus.click();',
            interaction,
        )

    def test_command_centre_is_visible_without_disabling_chat(self):
        source = (STATIC / "smi_command_centre.js").read_text(encoding="utf-8")
        self.assertIn('setOpen(true);', source)
        self.assertIn('setOpen(false);toggle.focus();', source)
        self.assertIn('stage.append(character)', source)

    def test_mobile_master_tools_escapes_scroll_clipping(self):
        styles = (STATIC / "smi_command_centre.css").read_text(encoding="utf-8")
        self.assertIn(".composer-left{overflow:visible!important", styles)
        self.assertIn(".attach-menu{position:fixed!important", styles)
        self.assertIn("max-height:min(67dvh,540px)", styles)
        self.assertIn("body:not(.smi-live-fullscreen)", styles)

    def test_master_tools_checks_follow_actual_drawer_state(self):
        source = (STATIC / "smi_chat_final.js").read_text(encoding="utf-8")
        self.assertIn('new MutationObserver(()=>{', source)
        self.assertIn('if(menu.classList.contains("show"))syncFunctionHealth()', source)
        self.assertIn('attributeFilter:["class"]', source)

    def test_full_room_preserves_real_chat_and_tool_handlers(self):
        styles = (STATIC / "smi_command_centre.css").read_text(encoding="utf-8")
        source = (STATIC / "smi_command_centre.js").read_text(encoding="utf-8")
        self.assertIn("position:fixed!important;inset:4px", styles)
        self.assertIn(".smi-command-universe", styles)
        self.assertIn('panel.querySelector(".smi-command-layout").after(universe)', source)
        self.assertIn('canonical.click()', source)
        self.assertIn('event.target?.id==="chat-form"&&active', source)
        self.assertIn('event.target?.id==="message"&&event.key==="Enter"', source)
        self.assertIn('setOpen(false)', source)
        self.assertNotIn("All Systems Operational", source)

    def test_mobile_organism_and_evidence_are_reachable(self):
        source = (STATIC / "smi_command_centre.js").read_text(encoding="utf-8")
        styles = (STATIC / "smi_command_centre.css").read_text(encoding="utf-8")
        self.assertIn('panel.dataset.mobileView="scene"', source)
        self.assertIn('panel.dataset.mobileView=tab.dataset.view', source)
        self.assertIn('if(tab.dataset.view==="evidence")refreshEvidence()', source)
        self.assertIn('data-mobile-view="anatomy"', styles)
        self.assertIn('data-mobile-view="evidence"', styles)
        self.assertIn('display:grid!important', styles)
        self.assertIn('smi-command-descriptive', source)

    def test_status_and_signals_remain_visible_above_command_room(self):
        source = (STATIC / "smi_command_centre.js").read_text(encoding="utf-8")
        styles = (STATIC / "smi_command_centre.css").read_text(encoding="utf-8")
        dashboard = (STATIC / "smi_sovereign_dashboard.js").read_text(encoding="utf-8")
        self.assertIn('statusButton.textContent="📊 SMI Status"', source)
        self.assertIn('signalsButton.textContent="◌ 21 Signals"', source)
        self.assertIn('statusToggle.click()', source)
        self.assertIn('details.open=true', source)
        self.assertIn('.smi-command-status-actions button', styles)
        self.assertIn('body.smi-status-open .smi-dashboard-layer{z-index:12500', styles)
        self.assertIn("if(panel.tagName==='DETAILS')panel.open=true", dashboard)
        self.assertIn('signals?.ready===true&&signals?.signals_valid===true', dashboard)
        self.assertIn('21 Signals endpoint unavailable · NOT PROVEN', dashboard)

    def test_live_dashboard_status_is_inline_and_fail_closed(self):
        source = (STATIC / "smi_command_centre.js").read_text(encoding="utf-8")
        styles = (STATIC / "smi_command_centre.css").read_text(encoding="utf-8")
        for token in ('smi-room-status','smi-room-status-grid','smi-room-gates',
                      'data-room-stat="signals"','data-room-stat="alignment"',
                      'data-room-gate="rollback"','data-room-gate="runtime_guard"',
                      'data-room-gate="isolation"','data-room-gate="founder"'):
            self.assertIn(token, source)
        self.assertIn('signals?.ready===true&&signals?.signals_valid===true', source)
        self.assertIn('Number(signals?.signal_count)===21', source)
        self.assertIn('checks.rollback_recovery===true', source)
        self.assertIn('checks.runtime_guard===true', source)
        self.assertIn('checks.isolation_recovery===true', source)
        self.assertIn('setRoom(roomGates.get("founder"),false', source)
        self.assertIn('credentials:"same-origin"', source)
        self.assertIn('if(signal.aborted)return', source)
        self.assertIn('.smi-room-status-grid', styles)
        self.assertIn('.smi-room-status [data-proven="true"]', styles)
        self.assertNotIn('All Systems Operational', source)

    def test_mobile_and_accessibility(self):
        source = (STATIC / "smi_command_centre.js").read_text(encoding="utf-8")
        styles = (STATIC / "smi_command_centre.css").read_text(encoding="utf-8")
        self.assertIn('aria-pressed', source)
        self.assertIn('event.key==="Escape"', source)
        self.assertIn("max-width:700px", styles)
        self.assertIn("prefers-reduced-motion:reduce", styles)


if __name__ == "__main__":
    unittest.main()
