"""Evidence-driven specialist assignment tests."""
import unittest

from oap.smi.alliance_agent_upgrade import plan_assurance_specialists
from oap.smi.alliance_assurance import review_assurance


class SpecialistUpgradeTests(unittest.TestCase):
    def test_missing_evidence_assigns_recovery_and_unsupported_claim_review(self):
        review = review_assurance("routing", {"london": True}, {})
        duties = {item.specialist: item for item in plan_assurance_specialists(review)}
        self.assertEqual(duties["Dozer"].evidence_keys, ("london",))
        self.assertEqual(duties["Thompson"].evidence_keys, ("london",))
        self.assertNotIn("Jones", duties)

    def test_contradictions_assign_independent_challenge(self):
        review = review_assurance("bank", {"ledger": True}, {"ledger": False})
        duties = {item.specialist: item for item in plan_assurance_specialists(review)}
        self.assertEqual(duties["Jones"].evidence_keys, ("ledger",))
        self.assertEqual(duties["Jackson"].evidence_keys, ("ledger",))
        self.assertNotIn("Brown", duties)

    def test_verified_evidence_preserved_and_no_worker_authority(self):
        review = review_assurance("mail", {"inbox": True}, {"inbox": True})
        assignments = plan_assurance_specialists(review)
        duties = {item.specialist: item for item in assignments}
        self.assertEqual(duties["Tank"].evidence_keys, ("inbox",))
        self.assertEqual(duties["Twin Two"].evidence_keys, ())
        self.assertTrue(all(item.advisory_only for item in assignments))


if __name__ == "__main__":
    unittest.main()
