"""SMI dashboard regression checks; no live-service readiness claims."""
import unittest
from pathlib import Path

PAGE = Path(__file__).resolve().parents[1] / 'mission_control/templates/smi_command_dashboard.html'

class SMIHumanoidDashboardContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = PAGE.read_text(encoding='utf-8')

    def test_navigation_routes(self):
        for route in ('/mission/smi', '/mission/war-room', '/mission/agents', '/movement', '/mission/brain'):
            with self.subTest(route=route):
                self.assertIn('href="' + route + '"', self.html)

    def test_dynamic_intelligence_links(self):
        self.assertIn('href="{{ control.href }}"', self.html)
        self.assertIn('href="{{ command.sovereign_ui.primary_route }}"', self.html)

    def test_inference_refresh_control(self):
        self.assertIn('id="inference-refresh" type="button"', self.html)
        self.assertIn('id="inference-state"', self.html)

    def test_accessibility_and_truth(self):
        self.assertIn('aria-label="SMI Character"', self.html)
        self.assertIn('Human Authority final', self.html)
        self.assertIn('Live/external runtime is intentionally excluded', self.html)

if __name__ == '__main__':
    unittest.main()
