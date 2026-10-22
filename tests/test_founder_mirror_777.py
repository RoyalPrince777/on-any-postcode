"""Unit tests for the non-executing Founder Mirror passport projections."""
import unittest

from oap.smi.founder_mirror_777 import (
    WHOLE_HUMAN_DIMENSIONS, agent_passport_projection, founder_passport,
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


if __name__ == "__main__":
    unittest.main()
