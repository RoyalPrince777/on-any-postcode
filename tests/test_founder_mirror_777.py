"""Unit tests for the non-executing Founder Mirror passport projections."""
import unittest

from oap.smi.founder_mirror_777 import (
    WHOLE_HUMAN_DIMENSIONS, agent_passport_projection, founder_passport, 
    founder_card_projection, agent_registry_passport_projections,
)


class FounderMirrorPassportTests(unittest.TestCase):
    def test_founder_is_one_brain_with_all_dimensions(self):
        passport = founder_passport()
        self.assertEqual(passport["primary_codename"], "N24-7")
        self.assertEqual(passport["brain_count"], 1)
        self.assertEqual(len(WHOLE_HUMAN_DIMENSIONS), 21)
        self.assertEqual(len(set(WHOLE_HUMAN_DIMENSIONS)), 21)

    def test_no_real_identity_document_or_founder_impersonation(self):
        passport = founder_passport()
        self.assertFalse(passport["government_id"])
        self.assertIsNone(passport["birth_certificate"]["data"])
        self.assertFalse(passport["permissions"]["can_approve_as_founder"])

    def test_agent_projection_preserves_existing_identity(self):
        source = {"agent_id": "NEO-001", "name": "Neo", "family_id": "matrix", "version": "1.0"}
        projected = agent_passport_projection(source)
        self.assertEqual(projected["agent_id"], source["agent_id"])
        self.assertEqual(projected["origin_certificate"]["version"], "1.0")
        self.assertFalse(projected["human_birth_certificate"])
        self.assertFalse(projected["can_approve_as_founder"])

    def test_missing_agent_id_rejected(self):
        with self.assertRaises(ValueError):
            agent_passport_projection({"name": "Invented"})


    def test_card_excludes_private_identity_data(self):
        card = founder_card_projection()
        self.assertEqual(card["codename"], "N24-7")
        self.assertEqual(card["whole_human_dimension_count"], 21)
        self.assertFalse(card["auth_grant"])
        self.assertNotIn("birth_certificate", card)
        self.assertNotIn("aliases", card)

    def test_registry_projection_rejects_duplicate_ids(self):
        agents = [{"agent_id": "NEO-001"}, {"agent_id": "NEO-001"}]
        with self.assertRaises(ValueError):
            agent_registry_passport_projections(agents)

    def test_registry_projection_preserves_order_and_does_not_mutate(self):
        agents = [{"agent_id": "NEO-001"}, {"agent_id": "FOX-001"}]
        original = [dict(agent) for agent in agents]
        passports = agent_registry_passport_projections(agents)
        self.assertEqual([p["agent_id"] for p in passports], ["NEO-001", "FOX-001"])
        self.assertEqual(agents, original)

    def test_registry_rejects_invalid_entries(self):
        for agents in (None, {}, [{"name": "Missing"}], ["bad"]):
            with self.subTest(agents=agents):
                with self.assertRaises(ValueError):
                    agent_registry_passport_projections(agents)


if __name__ == "__main__":
    unittest.main()
