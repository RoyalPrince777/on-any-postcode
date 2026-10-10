"""Regression contract for the SMI dashboard portrait truth boundary."""

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "mission_control/templates/smi_command_dashboard.html"
ASSET = ROOT / "static/oap/smi_global_intelligence_command_centre.png"


class SMIPortraitContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = PAGE.read_text(encoding="utf-8")

    def test_existing_artwork_is_present(self):
        self.assertTrue(ASSET.is_file())
        self.assertGreater(ASSET.stat().st_size, 0)

    def test_artwork_is_visible_without_background_crop(self):
        self.assertIn('src="/static/oap/smi_global_intelligence_command_centre.png"', self.html)
        self.assertIn("object-fit:contain", self.html)
        self.assertNotIn("background-size:auto 475px", self.html)
        self.assertNotIn("center 16% / auto 620px", self.html)

    def test_unverified_full_body_is_not_claimed(self):
        self.assertIn("full-body character asset not yet verified", self.html)
        self.assertIn("LIVE MOTION UNVERIFIED", self.html)

    def test_founder_navigation_still_exists(self):
        self.assertIn('href="/mission/war-room"', self.html)
        self.assertIn('href="/mission/agents"', self.html)


if __name__ == "__main__":
    unittest.main()
