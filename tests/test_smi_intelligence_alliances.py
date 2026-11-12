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


def test_jungle_and_hive_homes_preserve_passports_and_authority():
    from mission_control.intelligence_alliances import get_founder_alliance_board

    board = get_founder_alliance_board()
    homes = {home["id"]: home for home in board["family_homes"]}
    jungle = homes["jungle_book_home"]
    hive = homes["insect_hive"]
    assert jungle["world_id"] == "life"
    assert jungle["family_id"] == "jungle_book"
    assert len(jungle["members"]) == 10
    assert all(member["registered"] and member["agent_id"] for member in jungle["members"])
    den = jungle["groups"][0]
    assert den["id"] == "wolf_den"
    assert {member["name"] for member in den["members"]} == {"Akela", "Wolf Pack"}
    assert den["registered_collective_is_one_passport"] is True
    assert hive["world_id"] == "life"
    assert hive["family_id"] == "animal"
    assert {member["name"] for member in hive["members"]} == {"Queen Bee", "Bee Swarm"}
    assert all(member["registered"] is False and member["agent_id"] is None for member in hive["members"])
    assert hive["activation_condition"] == "real_authorised_distributed_work"
    assert board["can_execute"] is False



def test_jungle_family_references_are_not_agents_or_extra_passports():
    from mission_control.intelligence_alliances import get_founder_alliance_board

    board = get_founder_alliance_board()
    jungle = next(h for h in board["family_homes"] if h["id"] == "jungle_book_home")
    groups = {g["id"]: g for g in jungle["groups"]}
    assert set(groups) == {"wolf_den", "elephant_patrol", "monkey_kingdom", "jungle_community"}
    assert {m["name"] for m in groups["wolf_den"]["character_references"]} >= {
        "Raksha", "Father Wolf", "Grey Brother", "Wolf Cubs", "Phao", "Phaona", "Won-tolla"
    }
    assert {m["name"] for m in groups["elephant_patrol"]["members"]} == {"Colonel Hathi", "Hathi Jr"}
    assert {m["name"] for m in groups["elephant_patrol"]["character_references"]} == {
        "Winifred", "Elephant Patrol"
    }
    canonical_ids = [m["agent_id"] for m in jungle["members"]]
    assert len(canonical_ids) == len(set(canonical_ids)) == 10
    for group in groups.values():
        for ref in group["character_references"]:
            assert ref["agent_id"] is None
            assert ref["registered"] is False
            assert ref["ranking_eligible"] is False
            assert ref["can_execute"] is False
            assert ref["source_continuity"]
    assert board["can_execute"] is False


def test_bird_intelligence_reuses_animal_passports_without_vulture_crew():
    from mission_control import agents
    from mission_control.intelligence_alliances import get_founder_alliance_board

    board = get_founder_alliance_board()
    homes = {home["id"]: home for home in board["family_homes"]}
    birds = homes["bird_intelligence"]
    assert birds["world_id"] == "life"
    assert birds["family_id"] == "animal"
    assert birds["classification"] == "specialist_home_not_new_intelligence_world"
    assert {m["name"] for m in birds["members"]} == {"Owl", "Eagle", "Falcon"}
    passports = {a["name"]: a["agent_id"] for a in agents.AGENT_REGISTRY
                 if a["family_id"] == "animal"}
    assert all(m["registered"] and m["agent_id"] == passports[m["name"]]
               for m in birds["members"])
    assert birds["can_execute"] is False
    assert set(birds["excluded_character_references"]) == {
        "Buzzie", "Flaps", "Ziggy", "Dizzy"
    }
    assert "vulture_crew" not in {
        group["id"] for group in homes["jungle_book_home"]["groups"]
    }
    assert board["can_execute"] is False


def test_bird_specialists_have_unique_homes_and_canonical_passports():
    from mission_control.intelligence_alliances import get_founder_alliance_board

    board = get_founder_alliance_board()
    bird = next(h for h in board["family_homes"] if h["id"] == "bird_intelligence")
    assert {home["id"] for home in bird["homes"]} == {
        "owl_wisdom_grove", "eagle_high_nest", "falcon_flight_perch"
    }
    assert {home["member"]["name"] for home in bird["homes"]} == {
        "Owl", "Eagle", "Falcon"
    }
    assert len({home["member"]["agent_id"] for home in bird["homes"]}) == 3
    canonical = {m["name"]: m["agent_id"] for m in bird["members"]}
    for home in bird["homes"]:
        assert home["member"]["agent_id"] == canonical[home["member"]["name"]]
        assert home["home_system"] == "Life System"
        assert home["advisory_only"] is True
        assert home["execution_authority"] is False
    assert board["can_execute"] is False
