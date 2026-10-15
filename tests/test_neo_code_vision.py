"""Regression tests for the read-only Neo Matrix projection."""
import unittest

from mission_control.matrix_command_monitors import neo_code_vision, monitor_snapshot


class NeoCodeVisionTests(unittest.TestCase):
    def test_no_telemetry_is_not_green(self):
        neo = neo_code_vision()
        self.assertTrue(neo["registered"])
        self.assertEqual(neo["code_vision"]["state"], "not_connected")
        self.assertFalse(neo["anomaly_intelligence"]["all_clear_proven"])
        self.assertFalse(neo["full_green"])
        self.assertFalse(neo["true_path_recovery"]["execution_granted"])

    def test_evidence_backed_failure_is_reported_without_execution(self):
        neo = neo_code_vision({
            "oap-tv": {"state": "failed", "evidence": "incident:123"},
            "oap-world": {"state": "healthy", "evidence": "check:456"},
        })
        self.assertEqual(neo["anomaly_intelligence"]["confirmed_count"], 1)
        self.assertEqual(neo["anomaly_intelligence"]["findings"][0]["service"], "oap-tv")
        self.assertEqual(neo["true_path_recovery"]["state"], "requires_authorised_diagnosis")
        self.assertFalse(neo["true_path_recovery"]["recovery_verified"])
        self.assertFalse(neo["full_green"])

    def test_healthy_sample_does_not_prove_full_green(self):
        neo = neo_code_vision({"sample": {"state": "healthy", "evidence": "check:1"}})
        self.assertTrue(neo["anomaly_intelligence"]["all_clear_proven"])
        self.assertFalse(neo["full_green"])

    def test_unknown_does_not_count_as_healthy(self):
        neo = neo_code_vision({"sample": {"state": "unknown", "evidence": "check:2"}})
        self.assertFalse(neo["anomaly_intelligence"]["all_clear_proven"])

    def test_missing_evidence_and_invalid_state_fail_closed(self):
        for observation in (
            {"state": "healthy"},
            {"state": "healthy", "evidence": ""},
            {"state": "not_a_real_state", "evidence": "check:1"},
        ):
            with self.subTest(observation=observation):
                with self.assertRaises(ValueError):
                    neo_code_vision({"sample": observation})

    def test_monitor_includes_neo_without_invented_telemetry(self):
        snapshot = monitor_snapshot()
        self.assertIn("neo_monitor", snapshot)
        self.assertEqual(snapshot["neo_monitor"]["code_vision"]["state"], "not_connected")
        self.assertEqual(snapshot["telemetry_monitor"]["state"], "not_connected")
        self.assertFalse(snapshot["full_green"])


if __name__ == "__main__":
    unittest.main()
