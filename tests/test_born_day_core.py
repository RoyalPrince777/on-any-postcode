"""Born Day deterministic core checks."""
import unittest

from mission_control.born_day import akan_name, choose_weekday, weekday_from_date


class BornDayCoreTests(unittest.TestCase):
    def test_yawoada(self):
        self.assertEqual(weekday_from_date("1986-08-21"), "Thursday")
        self.assertEqual(akan_name("Thursday", "male"), "Yaw")
        self.assertEqual(akan_name("Thursday", "female"), "Yaa")

    def test_leap_day(self):
        self.assertEqual(weekday_from_date("2024-02-29"), "Thursday")

    def test_weekday_without_birthdate(self):
        self.assertEqual(choose_weekday(weekday="thursday"), "Thursday")

    def test_matching_inputs(self):
        self.assertEqual(choose_weekday(weekday="Thursday", birth_date="1986-08-21"), "Thursday")

    def test_reject_mismatch(self):
        with self.assertRaisesRegex(ValueError, "born_day_weekday_mismatch"):
            choose_weekday(weekday="Friday", birth_date="1986-08-21")

    def test_reject_invalid_dates(self):
        for value in ("2025-02-29", "1986-8-21", "not-a-date"):
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, "born_day_invalid_date"):
                weekday_from_date(value)

    def test_reject_missing_or_invalid_weekday(self):
        for kwargs in ({}, {"weekday": "Funday"}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                choose_weekday(**kwargs)


if __name__ == "__main__":
    unittest.main()
