import unittest
from mission_control.smi_dynamic_leaderboard_777 import dynamic_leaderboard

def candidate(name, score, verified=True):
    return {"name": name, "evidence_id": f"receipt:{name}",
            "verified": verified,
            "scores": {"relevance": score, "verified_quality": score,
                       "reliability": score, "collaboration": score, "safety": score}}

class DynamicLeaderboardTests(unittest.TestCase):
    def test_mission_relative_order(self):
        result = dynamic_leaderboard("World", [candidate("Akela", 60), candidate("Fox", 90)])
        self.assertEqual([r["name"] for r in result["ranked"]], ["Fox", "Akela"])
        self.assertTrue(all(r["authority_granted"] is False for r in result["ranked"]))

    def test_missing_proof_is_unranked_not_zero(self):
        result = dynamic_leaderboard("World", [candidate("Shere Khan", 100, False)])
        self.assertEqual(result["ranked"], [])
        self.assertEqual(result["unranked"][0]["reason"], "missing_verified_evidence")

    def test_no_new_authority(self):
        result = dynamic_leaderboard("World", [])
        self.assertEqual(result["authority"], ["Founder Final", "Guardian", "HRM"])
        self.assertTrue(result["no_permission_changes"])
        self.assertIsNone(result["overall_vpi"])

    def test_rejects_invalid_scores_and_duplicates(self):
        invalid = candidate("Fox", 110)
        self.assertEqual(len(dynamic_leaderboard("World", [invalid])["unranked"]), 1)
        with self.assertRaises(ValueError):
            dynamic_leaderboard("World", [candidate("Fox", 90), candidate("Fox", 80)])

if __name__ == "__main__":
    unittest.main()
