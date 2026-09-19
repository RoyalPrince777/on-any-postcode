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
        self.assertIn('state.textContent="Not proven"', source)
        self.assertIn('state.textContent="Unavailable"', source)
        self.assertIn('credentials:"same-origin"', source)

    def test_mobile_and_accessibility(self):
        source = (STATIC / "smi_command_centre.js").read_text(encoding="utf-8")
        styles = (STATIC / "smi_command_centre.css").read_text(encoding="utf-8")
        self.assertIn('aria-pressed', source)
        self.assertIn('event.key==="Escape"', source)
        self.assertIn("max-width:700px", styles)
        self.assertIn("prefers-reduced-motion:reduce", styles)


if __name__ == "__main__":
    unittest.main()
