"""Anti-biometric shield contract tests; no sensors or live-network calls."""
import unittest

from mission_control.anti_biometric_shield import (
    evidence_gate,
    is_raw_biometric_category,
    permission_decision,
)
from mission_control.private_smi_recognition import (
    EvidenceState,
    Observation,
    project_observation,
)


class AntiBiometricShieldTests(unittest.TestCase):
    def test_identity_and_behavioural_templates_are_blocked(self):
        for name in (
            "biometric", "Facial Recognition", "face-embedding", "fingerprint",
            "voiceprint", "gait", "typing pattern", "keystroke dynamics",
            "speaker identification", "iris", "biometric.face",
        ):
            with self.subTest(name=name):
                self.assertTrue(is_raw_biometric_category(name))
                self.assertEqual(
                    permission_decision(category=name, operation="store", consent=True),
                    {"allowed": False, "reason": "RAW_BIOMETRICS_BLOCKED"},
                )
                with self.assertRaisesRegex(ValueError, "raw biometric"):
                    Observation(name, "user", "now", True, EvidenceState.UNKNOWN, 0.0, "secret")

    def test_consented_voice_call_not_a_voiceprint(self):
        self.assertFalse(is_raw_biometric_category("voice"))
        self.assertTrue(permission_decision(
            category="voice", operation="observe", consent=True, destination="local"
        )["allowed"])

    def test_no_external_egress_and_location_minimisation(self):
        self.assertEqual(permission_decision(
            category="location", operation="export", consent=True, destination="external"
        )["reason"], "EXTERNAL_DESTINATION_BLOCKED")
        self.assertEqual(permission_decision(
            category="precise_location", operation="observe", consent=False
        )["reason"], "LOCATION_MINIMISATION")
        self.assertEqual(permission_decision(
            category="location", operation="profile", consent=True
        )["reason"], "LOCATION_MINIMISATION")
        self.assertTrue(permission_decision(
            category="location", operation="observe", consent=True, destination="local"
        )["allowed"])

    def test_unknown_flows_and_no_consent_fail_closed(self):
        for operation, destination in (("send", "local"), ("observe", "unverified")):
            self.assertFalse(permission_decision(
                category="text", operation=operation, consent=True, destination=destination
            )["allowed"])
        self.assertFalse(permission_decision(
            category="text", operation="observe", consent=False
        )["allowed"])

    def test_recognition_projection_never_leaks_biometric_even_if_bypassed(self):
        class UnsafeLegacyObservation:
            category = "voiceprint"
            permission_granted = True
        self.assertEqual(
            project_observation(UnsafeLegacyObservation(), founder_authenticated=True),
            {"status": "DENIED", "value": None},
        )

    def test_no_false_green_even_if_all_self_reported_flags_true(self):
        default = evidence_gate()
        self.assertEqual(default["status"], "UNKNOWN")
        self.assertTrue(default["missing_proof"])
        assert all(default[key] is False for key in (
            "android_protection_verified", "external_cctv_blockable",
            "universal_tracking_blocked", "guaranteed",
        ))
        checks = {key: True for key in default["missing_proof"]}
        result = evidence_gate(checks)
        self.assertEqual(result["status"], "REVIEW_REQUIRED")
        self.assertFalse(result["guaranteed"])
        self.assertFalse(result["android_protection_verified"])


if __name__ == "__main__":
    unittest.main()
