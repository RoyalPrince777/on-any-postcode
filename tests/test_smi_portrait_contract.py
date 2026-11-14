"""Regression contract for the one SMI visual command centre."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "mission_control/templates/smi_visual_home.html"
ASSET = ROOT / "static/oap/smi_global_intelligence_command_centre.png"

class SMIPortraitContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = PAGE.read_text(encoding="utf-8")

    def test_existing_artwork_is_present(self):
        self.assertTrue(ASSET.is_file())
        self.assertGreater(ASSET.stat().st_size, 0)

    def test_artwork_is_the_existing_smi_identity(self):
        self.assertIn("/static/oap/smi_global_intelligence_command_centre.png", self.html)
        self.assertIn("SMI central command", self.html)

    def test_unverified_telemetry_not_presented_as_live(self):
        self.assertIn("NOT CHECKED", self.html)
        self.assertIn("UNKNOWN", self.html)
        self.assertIn("No invented global counts", self.html)

    def test_founder_navigation_still_exists(self):
        self.assertIn('href="/mission/war-room"', self.html)
        self.assertIn('href="/mission/agents"', self.html)
        self.assertIn('href="/mission/ollama"', self.html)

if __name__ == "__main__":
    unittest.main()
