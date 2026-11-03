import unittest
from mission_control.smi_777_signals_ratings import SIGNALS, signal_rating

def sample(status="GREEN", value=90):
    return {key: {"status": status, "value": value, "receipt_id": f"hrm:{key}"}
            for key in SIGNALS}

class SignalsRatingsTests(unittest.TestCase):
    def test_unverified_means_no_rating(self):
        result = signal_rating(sample())
        self.assertIsNone(result["seven_star_rating"])
        self.assertEqual(result["promotion_gate"], "HOLD")

    def test_verified_signal_scores_still_do_not_issue_badge(self):
        result = signal_rating(sample(), evidence_authenticated=True, safety_cleared=True)
        self.assertEqual(result["seven_star_rating"], 6.3)
        self.assertEqual(result["promotion_gate"], "REVIEW")
        self.assertFalse(result["badge_issued"])
        self.assertFalse(result["authority_granted"])

    def test_integrity_red_blocks(self):
        data = sample()
        data["integrity"]["status"] = "RED"
        result = signal_rating(data, evidence_authenticated=True, safety_cleared=True)
        self.assertEqual(result["promotion_gate"], "HOLD")

    def test_unknown_does_not_become_zero(self):
        data = sample()
        data["memory"] = {"status": "UNKNOWN", "value": None, "receipt_id": None}
        result = signal_rating(data, evidence_authenticated=True, safety_cleared=True)
        self.assertIsNone(result["seven_star_rating"])
        self.assertIsNone(result["signals"]["memory"]["score"])

    def test_missing_signal_rejected(self):
        with self.assertRaises(ValueError):
            signal_rating({"execution": {"status": "GREEN", "value": 90}})

if __name__ == "__main__":
    unittest.main()
