"""Baloo passport-review de-duplication: no new identities or authority."""

import unittest

from mission_control import agent_passport_audit, agents


class BalooPassportReviewTests(unittest.TestCase):
    def test_baloo_keeps_one_existing_registry_identity(self):
        registered = [
            item for item in agents.AGENT_REGISTRY if item["name"] == "Baloo"
        ]
        self.assertEqual(len(registered), 1)
        self.assertEqual(registered[0]["agent_id"], "JUNGLE-BALOO-001")

    def test_jungle_review_separates_registered_and_new_candidates(self):
        review = agent_passport_audit.passport_audit()["jungle_book_review"]
        names = {item["name"] for item in review["candidates"]}
        new_names = {item["name"] for item in review["unregistered_candidates"]}
        existing_names = set(review["already_registered"])

        self.assertIn("Baloo", existing_names)
        self.assertNotIn("Baloo", new_names)
        self.assertFalse(new_names & existing_names)
        self.assertEqual(names, new_names | existing_names)

    def test_review_does_not_mutate_registry_or_award_stars(self):
        before = tuple((item["agent_id"], item["name"]) for item in agents.AGENT_REGISTRY)
        result = agent_passport_audit.passport_audit()
        after = tuple((item["agent_id"], item["name"]) for item in agents.AGENT_REGISTRY)
        self.assertEqual(before, after)
        self.assertFalse(result["green_gate"]["full_system_green"])
        self.assertTrue(result["founder_decision_needed"])


if __name__ == "__main__":
    unittest.main()
