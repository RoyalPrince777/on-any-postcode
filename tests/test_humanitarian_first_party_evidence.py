"""Regression tests for first-party humanitarian evidence and tracker linkage."""
import unittest

from mission_control.humanitarian_first_party_evidence import (
    first_party_verification_state,
    verify_original_finding,
)
from mission_control.humanitarian_emergency_tracker import humanitarian_emergency_snapshot


class FirstPartyHumanitarianEvidenceTests(unittest.TestCase):
    def test_empty_evidence_never_becomes_verified(self):
        result = verify_original_finding({"id": "oap-1", "claim": "A crisis exists", "authored_by": "OAP", "human_reviewed": True})
        self.assertEqual(result["status"], "unconfirmed")
        self.assertFalse(result["public_release_authorised"])

    def test_distinct_reviewed_evidence_and_human_review_required(self):
        finding = {"id": "oap-1", "claim": "Observed condition", "authored_by": "OAP", "human_reviewed": True,
                   "evidence": [{"id": "observation-1", "kind": "first_party_observation", "reviewed": True, "supports_claim": True},
                                {"id": "measurement-1", "kind": "first_party_measurement", "reviewed": True, "supports_claim": True}]}
        result = verify_original_finding(finding)
        self.assertEqual(result["status"], "internally_verified")
        self.assertFalse(result["public_release_authorised"])
        self.assertFalse(result["official_emergency_alert"])
        self.assertFalse(result["external_approval_required"])
        finding["human_reviewed"] = False
        self.assertEqual(verify_original_finding(finding)["status"], "unconfirmed")

    def test_duplicate_evidence_cannot_pass(self):
        evidence = {"id": "same", "kind": "first_party_observation", "reviewed": True, "supports_claim": True}
        result = verify_original_finding({"id": "1", "claim": "x", "authored_by": "OAP", "human_reviewed": True, "evidence": [evidence, evidence]})
        self.assertEqual(result["accepted_evidence_count"], 1)
        self.assertEqual(result["status"], "unconfirmed")

    def test_external_author_claim_cannot_become_oap_original(self):
        result = verify_original_finding({"id": "1", "claim": "x", "authored_by": "WHO", "human_reviewed": True,
            "evidence": [{"id": "1", "kind": "external_reference", "reviewed": True, "supports_claim": True},
                         {"id": "2", "kind": "external_reference", "reviewed": True, "supports_claim": True}]})
        self.assertEqual(result["origin"], "unestablished")
        self.assertEqual(result["status"], "unconfirmed")

    def test_existing_tracker_snapshot_has_unclaimed_first_party_state(self):
        snapshot = humanitarian_emergency_snapshot(live_fetch=False)
        self.assertEqual(snapshot["first_party_verification"], first_party_verification_state())
        self.assertEqual(snapshot["first_party_verification"]["verified_findings"], 0)


if __name__ == "__main__":
    unittest.main()
