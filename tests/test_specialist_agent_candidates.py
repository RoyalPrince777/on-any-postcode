"""Fail-closed tests for review-only SMI specialist candidates."""
import unittest

from mission_control import agents
from mission_control import specialist_agent_candidates as spec


class SpecialistAgentCandidateTests(unittest.TestCase):
    def test_exactly_21_original_candidates_in_12_families(self):
        self.assertEqual(len(spec.PROPOSED_AGENTS), 21)
        self.assertEqual(len(spec.SPECIALIST_FAMILIES), 12)
        self.assertEqual(len({r["review_key"] for r in spec.PROPOSED_AGENTS}), 21)

    def test_unchanged_canonical_78_and_no_name_collisions(self):
        self.assertEqual(len(agents.AGENT_REGISTRY), agents.LOCKED_AGENT_COUNT)
        report = spec.review_status()
        self.assertTrue(report["candidate_checks_passed"], report)
        self.assertFalse(report["registered_agent_count_changed"])
        self.assertEqual(report["draft_brief_completeness_percent"], 100.0)

    def test_candidates_cannot_execute_vote_or_claim_real_authority(self):
        for item in spec.PROPOSED_AGENTS:
            self.assertFalse(item["execution_enabled"])
            self.assertFalse(item["vote_eligible"])
            self.assertFalse(item["passport_issued"])
            self.assertFalse(item["real_world_authority"])
            self.assertIsNone(item["canonical_agent_id"])
            self.assertIsNone(item["career_stars"])
            self.assertEqual(item["performance_rating"], "UNRATED")
            self.assertFalse(item["permissions"])

    def test_fail_closed_if_candidate_collides_with_registry(self):
        report = spec.review_status(
            registered_agents=({"name": "Undercover Confidentiality Specialist"},),
            non_agent_system_names=("Guardian",),
        )
        self.assertFalse(report["candidate_checks_passed"])
        self.assertIn("Undercover Confidentiality Specialist", report["collisions"])

    def test_functional_names_not_character_codenames(self):
        old_codenames = ["Rowan","Vale","Hart","Quinn","Mercer","Cross","Nyx","Slate","Meridian","Ledger","Horizon","Atlas","Bastion","Threshold","Farpoint","Crosswind","Vector","Waypoint","Beacon","Cipher","Northstar"]
        names = [item["name"] for item in spec.PROPOSED_AGENTS]
        self.assertEqual(len(names), len(set(names)))
        self.assertTrue(set(names).isdisjoint(old_codenames))
        self.assertEqual(names[:3], [
            "Police Constable", "Police Sergeant", "Police Inspector",
        ])
        self.assertEqual(names[3:6], [
            "CID Detective Constable",
            "CID Detective Inspector",
            "CID Detective Chief Inspector",
        ])
        self.assertTrue(all(" " in name for name in names))
        self.assertTrue(all(
            item["review_key"].startswith("draft:")
            for item in spec.PROPOSED_AGENTS
        ))

    def test_live_readiness_never_inferred_from_brief_completeness(self):
        report = spec.review_status(
            registered_agents=(),
            non_agent_system_names=(),
        )
        self.assertIsNone(report["runtime_readiness_percent"])
        self.assertIsNone(report["overall_vpi_percent"])
        self.assertFalse(report["promotion_authorised"])

if __name__ == "__main__":
    unittest.main()
