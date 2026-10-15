"""Audit record constraints and truth-boundary tests."""
import unittest
from datetime import datetime, timezone

from oap.smi.organism_governance import evaluate_governance
from oap.smi.governance_decision_registry import record_decision


class GovernanceDecisionRegistryTests(unittest.TestCase):
    def setUp(self):
        self.when = datetime(2026, 10, 15, tzinfo=timezone.utc)
        self.ready = evaluate_governance(
            "Routing rollout", evidence_verified=True,
            independent_judicial_review=True, mandatory_controls_pass=True,
            advisory_votes=(("voters", "SUPPORT"),),
        )

    def make_record(self, review=None, **kwargs):
        defaults = dict(
            recorded_at=self.when, leadership_recommendation="Review routing",
            judicial_review_reference="judicial-report-1",
            evidence_references=("ci-run-123",),
        )
        defaults.update(kwargs)
        return record_decision("decision-1", review or self.ready, **defaults)

    def test_deterministic_evidence_record(self):
        first = self.make_record()
        self.assertEqual(first.record_hash, self.make_record().record_hash)
        self.assertEqual(len(first.record_hash), 64)
        self.assertEqual(first.execution_status, "NOT_AUTHORISED")

    def test_founder_approval_is_not_execution(self):
        record = self.make_record(founder_decision="APPROVED")
        self.assertEqual(record.founder_decision, "APPROVED")
        self.assertEqual(record.execution_status, "NOT_AUTHORISED")

    def test_blocked_proposal_cannot_be_approved(self):
        blocked = evaluate_governance(
            "Routing rollout", evidence_verified=False,
            independent_judicial_review=True, mandatory_controls_pass=True,
        )
        with self.assertRaises(ValueError):
            self.make_record(blocked, founder_decision="APPROVED")

    def test_missing_evidence_reference_rejected(self):
        with self.assertRaises(ValueError):
            self.make_record(evidence_references=())

    def test_missing_judicial_reference_rejected(self):
        with self.assertRaises(ValueError):
            self.make_record(judicial_review_reference=None)

    def test_naive_timestamp_rejected(self):
        with self.assertRaises(ValueError):
            self.make_record(recorded_at=datetime(2026, 10, 15))

    def test_previous_hash_changes_record(self):
        first = self.make_record()
        second = self.make_record(previous_record_hash=first.record_hash)
        self.assertNotEqual(first.record_hash, second.record_hash)
        self.assertEqual(second.previous_record_hash, first.record_hash)


if __name__ == "__main__":
    unittest.main()
