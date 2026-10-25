"""Review-only extensions preserve the original 78-agent SMI registry."""

import unittest

from mission_control import agents
from mission_control import specialist_agent_candidates as first
from mission_control import specialist_command_candidates as spec


class SpecialistCommandCandidateTests(unittest.TestCase):
    def test_six_sections_with_twenty_one_unique_descriptive_agents(self):
        self.assertEqual(len(spec.EXTENDED_FAMILIES), 6)
        self.assertEqual(len(spec.EXTENDED_AGENTS), 21)
        self.assertEqual(len({a["review_key"] for a in spec.EXTENDED_AGENTS}), 21)
        self.assertEqual(len({a["name"] for a in spec.EXTENDED_AGENTS}), 21)

    def test_complete_official_british_army_two_track_reference(self):
        ranks = spec.UK_ARMY_RANK_REFERENCE
        self.assertEqual(len(ranks["soldier"]), 7)
        self.assertEqual(len(ranks["officer"]), 12)
        self.assertEqual(ranks["soldier"][0], "Private")
        self.assertEqual(ranks["officer"][-1], "Field Marshal")
        self.assertTrue(spec.review_status()["rank_reference_valid"])

    def test_old_passports_and_draft_roster_are_unchanged(self):
        self.assertEqual(len(agents.AGENT_REGISTRY), agents.LOCKED_AGENT_COUNT)
        self.assertEqual(len(first.PROPOSED_AGENTS), 21)
        report = spec.review_status()
        self.assertTrue(report["candidate_checks_passed"], report)
        self.assertEqual(report["total_review_candidate_count"], 42)
        self.assertFalse(report["registered_agent_count_changed"])
        self.assertEqual(report["new_passports_issued"], 0)
        self.assertTrue(report["matrix_core_unchanged"])
        self.assertTrue(report["guardian_is_non_agent_system"])

    def test_fail_closed_no_new_powers_voting_stars_or_live_claim(self):
        for a in spec.EXTENDED_AGENTS:
            self.assertFalse(a["execution_enabled"])
            self.assertFalse(a["vote_eligible"])
            self.assertFalse(a["real_world_authority"])
            self.assertFalse(a["passport_issued"])
            self.assertFalse(a["guardian_gate_overridden"])
            self.assertFalse(a["permissions"])
            self.assertFalse(a["provider_ids"])
            self.assertIsNone(a["canonical_agent_id"])
            self.assertIsNone(a["career_stars"])
        report = spec.review_status()
        self.assertIsNone(report["live_readiness_percent"])
        self.assertIsNone(report["overall_vpi_percent"])
        self.assertFalse(report["production_green"])

    def test_all_six_functions_present_without_hijacking_core_systems(self):
        families = {a["family_key"] for a in spec.EXTENDED_AGENTS}
        self.assertEqual(families, {
            "military", "presidential", "matrix_review", "chess",
            "guardian_review", "imperial",
        })
        self.assertNotIn("Guardian", {a["name"] for a in spec.EXTENDED_AGENTS})
        self.assertNotIn("Neo", {a["name"] for a in spec.EXTENDED_AGENTS})
        self.assertNotIn("Emperor", {a["name"] for a in spec.EXTENDED_AGENTS})

    def test_reject_name_collision_with_existing_draft_and_system(self):
        collision = {"name": "Chess Opening Research Agent"}
        self.assertFalse(spec.review_status(other_candidates=(collision,))["candidate_checks_passed"])
        self.assertFalse(spec.review_status(
            system_names=("Military Chain-of-Command Analyst",)
        )["candidate_checks_passed"])


if __name__ == "__main__":
    unittest.main()
