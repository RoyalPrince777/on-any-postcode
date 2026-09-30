"""Regression tests for the reusable, non-publishing decade admission guard."""

import unittest

from mission_control.awards_eligibility import check_decade_nomination

GOOD = {
    "nominee_name": "Example artist",
    "award_type": "Music",
    "achievement_date": "2020-01-01",
    "evidence_reference": "archive:example-001",
}


class DecadeEligibilityTests(unittest.TestCase):
    def check(self, record, expected, first=2020, last=2029):
        self.assertEqual(
            check_decade_nomination(record, first_year=first, last_year=last),
            expected,
        )

    def test_first_and_last_day_inclusive(self):
        self.check(GOOD, (True, "eligible_for_review"))
        self.check({**GOOD, "achievement_date": "2029-12-31"}, (True, "eligible_for_review"))

    def test_boundary_exclusion(self):
        self.check({**GOOD, "achievement_date": "2019-12-31"}, (False, "outside_decade"))
        self.check({**GOOD, "achievement_date": "2030-01-01"}, (False, "outside_decade"))

    def test_historical_row_fails_closed(self):
        old = {k: GOOD[k] for k in ("nominee_name", "award_type")}
        self.check(old, (False, "missing_evidence"))
        self.check({**old, "evidence_reference": "archive:1"}, (False, "missing_or_invalid_achievement_date"))

    def test_required_fields(self):
        self.check({**GOOD, "nominee_name": "  "}, (False, "missing_nominee"))
        self.check({**GOOD, "award_type": ""}, (False, "missing_category"))
        self.check({**GOOD, "evidence_reference": "  "}, (False, "missing_evidence"))
        self.check(None, (False, "invalid_record"))

    def test_strict_iso_date(self):
        for bad in ("2020-02-30", "2020-1-01", "not-a-date", "", None, 20200101):
            self.check({**GOOD, "achievement_date": bad}, (False, "missing_or_invalid_achievement_date"))

    def test_decade_not_assumed(self):
        self.check({**GOOD, "achievement_date": "2030-01-01"}, (True, "eligible_for_review"), 2030, 2039)
        for first, last in ((2020, 2028), (2020, 2030), (2029, 2020), (0, 9), (9991, 10000)):
            with self.subTest(first=first, last=last), self.assertRaises(ValueError):
                check_decade_nomination(GOOD, first_year=first, last_year=last)
        with self.assertRaises(TypeError):
            check_decade_nomination(GOOD, first_year=True, last_year=2029)

    def test_eligibility_does_not_assert_winner(self):
        self.assertEqual(
            check_decade_nomination({**GOOD, "status": "pending", "winner": False}, first_year=2020, last_year=2029),
            (True, "eligible_for_review"),
        )


if __name__ == "__main__":
    unittest.main()
