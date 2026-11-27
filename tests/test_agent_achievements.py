"""Evidence-gated lifetime achievement ranking tests."""
import unittest

from mission_control import agent_achievements, agents


class AgentAchievementsTests(unittest.TestCase):
    def setUp(self):
        self.first = agents.AGENT_REGISTRY[0]["agent_id"]
        self.second = agents.AGENT_REGISTRY[1]["agent_id"]
        self.judges = dict.fromkeys(agent_achievements.REQUIRED_JUDGES, True)

    def award(self, agent_id=None, movement="m1", kind="minor"):
        return {"agent_id": agent_id or self.first, "movement_id": movement,
                "kind": kind, "evidence": "commit:abc123",
                "judges": dict(self.judges), "referee_approved": True}

    def test_empty_ledger_has_no_earned_stars(self):
        rankings = agent_achievements.career_rankings([])
        self.assertEqual(len(rankings), len(agents.AGENT_REGISTRY))
        self.assertTrue(all(row["achievement_stars"] == 0 for row in rankings))

    def test_unlimited_individual_stars_and_separate_contributors(self):
        awards = [self.award(movement=f"m{i}", kind="protocol") for i in range(3)]
        awards.append(self.award(self.second, "m0", "minor"))
        totals = {r["agent_id"]: r["achievement_stars"]
                  for r in agent_achievements.career_rankings(awards)}
        self.assertEqual(totals[self.first], 15)
        self.assertEqual(totals[self.second], 1)

    def test_duplicate_is_rejected(self):
        with self.assertRaises(ValueError):
            agent_achievements.career_rankings([self.award(), self.award()])

    def test_invalid_agent_rejected(self):
        with self.assertRaises(ValueError):
            agent_achievements.career_rankings([self.award("not-an-agent")])

    def test_unapproved_judge_rejected(self):
        award = self.award()
        award["judges"]["gorilla"] = False
        with self.assertRaises(ValueError):
            agent_achievements.career_rankings([award])

    def test_referee_required(self):
        award = self.award()
        award["referee_approved"] = False
        with self.assertRaises(ValueError):
            agent_achievements.career_rankings([award])


if __name__ == "__main__":
    unittest.main()
