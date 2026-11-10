"""Recovered alliance presentation must not create passports or authority."""
import unittest

from mission_control import agents, intelligence_alliances, war_room


class SmiIntelligenceAllianceTests(unittest.TestCase):
    def test_smi_visible_above_agent_rankings(self):
        board = intelligence_alliances.get_founder_alliance_board()
        self.assertEqual(board["smi"]["kind"], "intelligence_brain")
        self.assertFalse(board["smi"]["career_ranking_eligible"])
        self.assertEqual(board["human_authority"], "Founder Final")
        self.assertFalse(board["can_approve"])
        self.assertFalse(board["can_execute"])

    def test_six_preserved_alliances_without_new_passports(self):
        before = len(agents.AGENT_REGISTRY)
        board = intelligence_alliances.get_founder_alliance_board()
        self.assertEqual(
            {a["id"] for a in board["alliances"]},
            {"mission_impossible", "terminator", "predator",
             "transformers", "jungle_book", "batman"},
        )
        self.assertEqual(before, len(agents.AGENT_REGISTRY))
        for alliance in board["alliances"]:
            if alliance["id"] != "jungle_book":
                self.assertTrue(all(
                    member["agent_id"] is None and not member["ranking_eligible"]
                    for member in alliance["members"]
                ))

    def test_jungle_book_reuses_canonical_passports_and_excludes_kaa(self):
        board = intelligence_alliances.get_founder_alliance_board()
        jungle = next(a for a in board["alliances"] if a["id"] == "jungle_book")
        expected = {
            a["agent_id"] for a in agents.AGENT_REGISTRY
            if a["family_id"] == "jungle_book"
        }
        self.assertEqual({a["agent_id"] for a in jungle["members"]}, expected)
        self.assertNotIn("Kaa", {a["name"] for a in jungle["members"]})

    def test_smi_board_visible_in_existing_read_only_war_room(self):
        dashboard = war_room.get_war_room_dashboard()
        self.assertEqual(
            dashboard["intelligence_alliance_board"]["smi"]["name"], "SMI"
        )
        self.assertFalse(dashboard["controls_enabled"])
        self.assertFalse(dashboard["can_approve"])
        self.assertFalse(dashboard["can_execute"])
        self.assertIn("agent_achievement_rankings", dashboard)

    def test_threat_models_not_terminator_agents(self):
        board = intelligence_alliances.get_founder_alliance_board()
        terminator = next(a for a in board["alliances"] if a["id"] == "terminator")
        self.assertEqual(terminator["threat_models_not_agents"], ("Skynet", "Legion"))
        self.assertEqual(terminator["status"], "existing_agent_capability_overlay_only")


if __name__ == "__main__":
    unittest.main()
