"""Real SQLite persistence, chain-integrity and fail-closed tests."""
import sqlite3
import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path

from oap.smi.governance_audit_store import GovernanceAuditStore
from oap.smi.governance_decision_registry import record_decision
from oap.smi.organism_governance import evaluate_governance


class GovernanceAuditStoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "audit.sqlite3"
        self.store = GovernanceAuditStore(self.path)
        self.review = evaluate_governance(
            "OAP governance", evidence_verified=True,
            independent_judicial_review=True, mandatory_controls_pass=True,
        )

    def record(self, decision_id, previous=None):
        return record_decision(
            decision_id, self.review, recorded_at=datetime(2026, 10, 15, tzinfo=UTC),
            leadership_recommendation="Proceed to Founder review",
            judicial_review_reference="review-1", evidence_references=("ci-1",),
            previous_record_hash=previous,
        )

    def test_survives_reopen_and_verifies_chain(self):
        first = self.record("one")
        self.store.append(first)
        second = self.record("two", first.record_hash)
        GovernanceAuditStore(self.path).append(second)
        rows = GovernanceAuditStore(self.path).verify()
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[-1]["previous_record_hash"], first.record_hash)

    def test_rejects_wrong_previous_hash(self):
        self.store.append(self.record("one"))
        with self.assertRaises(ValueError):
            self.store.append(self.record("two"))
        self.assertEqual(len(self.store.verify()), 1)

    def test_duplicate_id_is_rejected(self):
        self.store.append(self.record("one"))
        with self.assertRaises(sqlite3.IntegrityError):
            self.store.append(self.record("one", self.record("one").record_hash))

    def test_tampering_blocks_reads_and_writes(self):
        self.store.append(self.record("one"))
        with sqlite3.connect(self.path) as db:
            db.execute("UPDATE governance_audit SET payload = replace(payload, 'OAP governance', 'OTHER')")
        with self.assertRaises(ValueError):
            self.store.verify()
        with self.assertRaises(ValueError):
            self.store.append(self.record("two"))

    def test_no_implicit_execution_authority(self):
        self.store.append(self.record("one"))
        self.assertEqual(self.store.verify()[0]["execution_status"], "NOT_AUTHORISED")


if __name__ == "__main__":
    unittest.main()
