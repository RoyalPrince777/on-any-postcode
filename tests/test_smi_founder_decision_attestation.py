"""Real HMAC Founder decision signature and adversarial verification tests."""
import unittest
from dataclasses import replace
from datetime import UTC, datetime, timedelta

from oap.smi.founder_decision_attestation import (
    sign_founder_decision,
    verify_founder_decision,
)
from oap.smi.governance_decision_registry import record_decision
from oap.smi.organism_governance import evaluate_governance


class FounderDecisionAttestationTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 10, 15, tzinfo=UTC)
        self.secret = b"test-only-secret-with-adequate-entropy-123456"
        self.review = evaluate_governance(
            "OAP governance", evidence_verified=True,
            independent_judicial_review=True, mandatory_controls_pass=True,
        )
        self.record = record_decision(
            "decision-1", self.review, recorded_at=self.now,
            leadership_recommendation="Founder review",
            judicial_review_reference="review-1", evidence_references=("ci-1",),
        )
        self.proof = sign_founder_decision(
            self.record, founder_id="founder", decision="APPROVED",
            issued_at=self.now, expires_at=self.now + timedelta(minutes=5),
            secret=self.secret,
        )

    def valid(self, proof=None, record=None, now=None, secret=None, founder="founder"):
        return verify_founder_decision(
            self.record if record is None else record,
            self.proof if proof is None else proof,
            expected_founder_id=founder,
            now=self.now if now is None else now,
            secret=self.secret if secret is None else secret,
        )

    def test_valid_signature(self):
        self.assertTrue(self.valid())

    def test_forged_signature_rejected(self):
        self.assertFalse(self.valid(replace(self.proof, signature="0" * 64)))

    def test_changed_decision_rejected(self):
        self.assertFalse(self.valid(replace(self.proof, decision="REJECTED")))

    def test_changed_record_rejected(self):
        self.assertFalse(self.valid(replace(self.record, record_hash="0" * 64)))

    def test_wrong_founder_rejected(self):
        self.assertFalse(self.valid(founder="other"))

    def test_wrong_secret_rejected(self):
        self.assertFalse(self.valid(secret=b"other-test-secret-with-enough-bytes-123456"))

    def test_expired_rejected(self):
        self.assertFalse(self.valid(now=self.now + timedelta(minutes=5)))

    def test_future_dated_rejected(self):
        self.assertFalse(self.valid(now=self.now - timedelta(seconds=1)))

    def test_blocked_governance_cannot_be_signed_as_approved(self):
        blocked = evaluate_governance(
            "Blocked", evidence_verified=False,
            independent_judicial_review=False, mandatory_controls_pass=False,
        )
        record = record_decision(
            "blocked", blocked, recorded_at=self.now,
            leadership_recommendation="Stop",
        )
        with self.assertRaises(ValueError):
            sign_founder_decision(
                record, founder_id="founder", decision="APPROVED",
                issued_at=self.now, expires_at=self.now + timedelta(minutes=1),
                secret=self.secret,
            )

    def test_weak_secret_rejected(self):
        with self.assertRaises(ValueError):
            sign_founder_decision(
                self.record, founder_id="founder", decision="APPROVED",
                issued_at=self.now, expires_at=self.now + timedelta(minutes=1),
                secret=b"short",
            )


if __name__ == "__main__":
    unittest.main()
