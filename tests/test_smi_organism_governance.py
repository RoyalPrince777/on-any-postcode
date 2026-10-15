"""Bounded governance contract tests (no simulated agent execution)."""
import unittest

from oap.smi.organism_governance import (
    ASSIGNMENTS,
    DIMENSIONS,
    FUNCTIONS,
    MASTER_VITALS,
    evaluate_governance,
)


class OrganismGovernanceTests(unittest.TestCase):
    def test_canonical_dimensions_and_vitals_remain_distinct(self):
        self.assertEqual(len(DIMENSIONS), 13)
        self.assertEqual(len(set(DIMENSIONS)), 13)
        self.assertEqual(len(MASTER_VITALS), 10)
        self.assertEqual(len(set(MASTER_VITALS)), 10)

    def test_every_dimension_has_one_governance_home(self):
        self.assertEqual(set(ASSIGNMENTS), set(FUNCTIONS))
        assigned = [dimension for key in FUNCTIONS for dimension in ASSIGNMENTS[key]]
        self.assertEqual(set(assigned), set(DIMENSIONS))
        self.assertEqual(len(assigned), len(set(assigned)))

    def test_votes_cannot_override_failed_mandatory_controls(self):
        result = evaluate_governance(
            "SIKA launch", evidence_verified=True,
            independent_judicial_review=True, mandatory_controls_pass=False,
            advisory_votes=(("leaders", "SUPPORT"), ("judges", "SUPPORT"),
                            ("voters", "SUPPORT")),
        )
        self.assertEqual(result.verdict, "BLOCKED")
        self.assertFalse(result.authorised)

    def test_missing_independent_review_blocks(self):
        result = evaluate_governance(
            "OAP routing", evidence_verified=True,
            independent_judicial_review=False, mandatory_controls_pass=True,
        )
        self.assertEqual(result.verdict, "BLOCKED")

    def test_verified_proposal_still_requires_founder(self):
        result = evaluate_governance(
            "OAP routing", evidence_verified=True,
            independent_judicial_review=True, mandatory_controls_pass=True,
        )
        self.assertEqual(result.verdict, "READY_FOR_FOUNDER_REVIEW")
        self.assertTrue(result.founder_approval_required)
        self.assertFalse(result.authorised)

    def test_reject_unrecognised_votes(self):
        with self.assertRaises(ValueError):
            evaluate_governance(
                "Test", evidence_verified=True, independent_judicial_review=True,
                mandatory_controls_pass=True, advisory_votes=(("unknown", "SUPPORT"),),
            )


if __name__ == "__main__":
    unittest.main()
