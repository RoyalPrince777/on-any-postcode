"""Regression gates for SMI A1-A7 read-only War Room projection."""
import unittest
from mission_control.war_room import _a1_a7_evidence_projection


class SmiAutonomyProjectionTests(unittest.TestCase):
    def test_ladder_is_single_smi_and_cannot_execute(self):
        view = _a1_a7_evidence_projection([])
        self.assertEqual(view["model"], "one_intelligence_seven_operating_levels")
        self.assertEqual(len(view["levels"]), 7)
        self.assertEqual([x["id"] for x in view["levels"]], [f"A{i}" for i in range(1, 8)])
        self.assertIsNone(view["highest_certified_level"])
        self.assertFalse(view["can_execute"])
        self.assertFalse(view["can_approve"])
        self.assertTrue(view["founder_final"])

    def test_portfolio_stars_never_auto_promote_autonomy(self):
        view = _a1_a7_evidence_projection([{"stars": 5}] * 21)
        self.assertEqual(view["portfolio_rated_areas"], 21)
        self.assertFalse(view["portfolio_proves_autonomy"])
        self.assertTrue(all(not level["certified"] for level in view["levels"]))
        self.assertTrue(all(level["locked"] for level in view["levels"][5:]))


if __name__ == "__main__":
    unittest.main()
