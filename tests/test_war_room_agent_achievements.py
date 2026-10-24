"""Ensure War Room displays achievement rankings without granting award authority."""
import unittest

from mission_control import agents, war_room


class WarRoomAgentAchievementTests(unittest.TestCase):
    def test_read_only_zero_baseline(self):
        dashboard = war_room.get_war_room_dashboard()
        section = dashboard["agent_achievement_rankings"]
        self.assertEqual(section["status"], "read_only_unawarded")
        self.assertEqual(section["awarded_movements"], 0)
        self.assertTrue(section["separate_from_readiness_ratings"])
        self.assertEqual(len(section["ranking"]), len(agents.AGENT_REGISTRY))
        self.assertTrue(all(item["achievement_stars"] == 0 for item in section["ranking"]))
        self.assertFalse(dashboard["can_approve"])
        self.assertFalse(dashboard["can_execute"])


if __name__ == "__main__":
    unittest.main()
