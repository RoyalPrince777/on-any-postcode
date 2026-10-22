import unittest
from mission_control.smi_777_merit_ladder import assess_merit, WEIGHTS

def scores(value):
    return {key: value for key in WEIGHTS}

class MeritLadderTests(unittest.TestCase):
    def test_no_proof_means_hold_even_with_100(self):
        result = assess_merit(scores(100))
        self.assertEqual(result["proposed_band"], "777 Grandmaster")
        self.assertEqual(result["decision"], "HOLD")
        self.assertFalse(result["badge_issued"])
        self.assertFalse(result["authority_granted"])

    def test_seven_distinct_conflict_free_reviews_required(self):
        reviews = tuple({"reviewer_id": f"reviewer-{i}", "independent": True,
                         "conflict_of_interest": False} for i in range(7))
        result = assess_merit(scores(98), evidence_receipts=("hrm:123",),
                              safety_cleared=True, independent_review_cleared=True,
                              peer_reviews=reviews, candidate_id="candidate")
        self.assertEqual(result["decision"], "ELIGIBLE_FOR_HRM_VERIFICATION")
        self.assertFalse(result["receipt_authenticity_verified"])
        self.assertFalse(result["badge_issued"])

    def test_self_vote_blocks(self):
        reviews = tuple({"reviewer_id": f"r{i}", "independent": True,
                         "conflict_of_interest": False} for i in range(6)) + (
                         {"reviewer_id": "candidate", "independent": True,
                          "conflict_of_interest": False},)
        result = assess_merit(scores(100), evidence_receipts=("hrm:123",),
                              safety_cleared=True, independent_review_cleared=True,
                              peer_reviews=reviews, candidate_id="candidate")
        self.assertEqual(result["decision"], "HOLD")

    def test_invalid_scores(self):
        with self.assertRaises(ValueError):
            assess_merit(scores(101))
        with self.assertRaises(ValueError):
            assess_merit({"safety": 90})

if __name__ == "__main__":
    unittest.main()
