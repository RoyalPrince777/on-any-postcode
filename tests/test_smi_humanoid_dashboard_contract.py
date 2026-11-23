"""Canonical SMI command-centre visual contract; no simulated operational proof."""
import unittest
from pathlib import Path

PAGE = Path(__file__).resolve().parents[1] / "mission_control/templates/smi_visual_home.html"


class SMIHumanoidDashboardContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = PAGE.read_text(encoding="utf-8")

    def test_navigation_routes(self):
        for route in (
            "/mission/smi",
            "/mission/ollama",
            "/mission/war-room",
            "/mission/agents",
            "/movement",
            "/mission/brain",
            "/mission/organism",
        ):
            with self.subTest(route=route):
                self.assertIn('href="' + route + '"', self.html)

    def test_one_conversation_entry_with_auto_mode(self):
        self.assertIn('class="smi-talk-primary"', self.html)
        self.assertIn("AUTO 3 / 7 / 21", self.html)
        self.assertIn('aria-label="Secondary intelligence routes"', self.html)

    def test_evidence_only_on_demand(self):
        self.assertIn('href="/mission/smi/status"', self.html)
        self.assertNotIn("setInterval(", self.html)

    def test_ambient_companion_presence_never_starts_private_chat(self):
        self.assertIn('data-smi-welcome', self.html)
        self.assertIn('Welcome back to your world.', self.html)
        self.assertIn('smiCompanionIdle', self.html)
        self.assertIn('prefers-reduced-motion:reduce', self.html)
        self.assertIn('data-smi-visible', self.html)
        self.assertIn("frame.dataset.src", self.html)
        self.assertIn("frame.removeAttribute('src')", self.html)
        self.assertNotIn('data-smi-play', self.html)
        self.assertNotIn('data-smi-motion-pause', self.html)
        self.assertIn("oap-smi-visual-state-v1", self.html)
        self.assertIn("event.source !== frame.contentWindow", self.html)
        self.assertIn("event.origin !== window.location.origin", self.html)
        self.assertIn("Listening", self.html)
        self.assertIn("Thinking", self.html)
        self.assertIn("Speaking", self.html)
        self.assertIn("Stopped", self.html)
        self.assertIn("data-smi-visual-state", self.html)

    def test_accessibility_and_truth(self):
        self.assertIn('aria-label="SMI central command"', self.html)
        self.assertIn("NOT CHECKED", self.html)
        self.assertIn("No invented global counts", self.html)


if __name__ == "__main__":
    unittest.main()
