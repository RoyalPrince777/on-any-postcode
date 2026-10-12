"""Contract tests for Founder-private recognition. No devices or production calls."""
import unittest

from mission_control.private_smi_recognition import (
    EvidenceState,
    Observation,
    project_observation,
    recognition_authorizes_action,
)


class RecognitionContractTests(unittest.TestCase):
    def setUp(self):
        self.observation = Observation(
            category="health",
            source="user_report",
            observed_at="2026-10-12T00:00:00Z",
            permission_granted=True,
            state=EvidenceState.UNKNOWN,
            confidence=0.0,
            value="example-private-value",
        )

    def test_no_founder_auth_leaks_nothing(self):
        result = project_observation(self.observation, founder_authenticated=False)
        self.assertEqual(result, {"status": "DENIED", "value": None})

    def test_authorized_observation_is_advisory_not_identity(self):
        result = project_observation(self.observation, founder_authenticated=True)
        self.assertEqual(result["status"], "ADVISORY_ONLY")
        self.assertFalse(result["identity_verified"])
        self.assertFalse(result["action_authorized"])
        self.assertTrue(result["sensitive"])

    def test_no_consent_denies(self):
        obs = Observation("location", "gps", "now", False, EvidenceState.VERIFIED, 1.0, "private")
        self.assertEqual(project_observation(obs, founder_authenticated=True)["status"], "DENIED")

    def test_recognition_never_grants_action(self):
        self.assertFalse(recognition_authorizes_action(observation=self.observation))

    def test_invalid_confidence_rejected(self):
        with self.assertRaises(ValueError):
            Observation("face", "camera", "now", True, EvidenceState.ESTIMATED, 1.2, "x")


if __name__ == "__main__":
    unittest.main()
