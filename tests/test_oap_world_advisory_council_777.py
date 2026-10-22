"""Regression tests for the non-executing SMI 21 World council."""
import unittest

from mission_control.oap_world_advisory_council_777 import advisory_council


class AdvisoryCouncilTests(unittest.TestCase):
    def test_twenty_one_roles_and_seven_decisions(self):
        council = advisory_council()
        self.assertEqual(len(council["roles"]), 21)
        self.assertEqual(len({r["name"] for r in council["roles"]}), 21)
        self.assertEqual([r["number"] for r in council["rounds"]], list(range(1, 8)))

    def test_pack_preserved(self):
        self.assertEqual(advisory_council()["permanent_wolf_pack"],
                         ["Akela", "Raksha", "Father Wolf", "Grey Brother", "Phao"])

    def test_no_live_execution_or_vote_claims(self):
        council = advisory_council()
        self.assertEqual(council["status"], "advisory_only")
        self.assertTrue(council["founder_final_required"])
        self.assertFalse(council["live_agent_votes_verified"])
        self.assertFalse(council["agent_runtime_activated"])
        self.assertIsNone(council["implementation_vpi"])

    def test_fail_closed_contract(self):
        locked = advisory_council()["blocked_capabilities"]
        self.assertIn("real_world_dispatch", locked)
        self.assertIn("payment_capture", locked)
        self.assertIn("hidden_tracking", locked)
        self.assertIn("autonomous_approval", locked)

    def test_mutation_does_not_change_canonical_advice(self):
        council = advisory_council()
        council["roles"].clear()
        council["rounds"].clear()
        self.assertEqual(len(advisory_council()["roles"]), 21)
        self.assertEqual(len(advisory_council()["rounds"]), 7)


if __name__ == "__main__":
    unittest.main()
