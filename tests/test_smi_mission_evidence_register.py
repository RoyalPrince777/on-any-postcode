"""SMI 44-mission signal register regression tests."""
import unittest

from mission_control.smi_mission_evidence_register import (
    all_mission_statuses,
    load_register,
    mission_status,
)


class TestMissionEvidenceRegister(unittest.TestCase):
    def test_44_missions_registered(self):
        self.assertEqual(len(load_register()["missions"]), 44)

    def test_no_fabricated_percentages(self):
        for mission in all_mission_statuses():
            self.assertIsNone(mission["overall_percent"])
            self.assertIsNone(mission["signal_percentage"])
            self.assertFalse(mission["green_100"])
            self.assertEqual(mission["signal_count"], 73)

    def test_unknown_mission_fails(self):
        with self.assertRaises(ValueError):
            mission_status(45)

    def test_unrecognised_signal_fails(self):
        register = load_register()
        register["missions"][0]["signals"]["states"]["invented.signal"] = "proven"
        with self.assertRaises(ValueError):
            mission_status(1, register=register)

    def test_unverified_claim_does_not_promote(self):
        register = load_register()
        register["missions"][0]["signals"]["states"]["crown.truth_mode"] = "proven"
        result = mission_status(1, register=register)
        self.assertIsNone(result["signal_percentage"])
        self.assertFalse(result["green_100"])


if __name__ == "__main__":
    unittest.main()
