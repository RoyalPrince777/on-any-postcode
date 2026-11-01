"""Fail closed if known Meta-owned tracking or data transfer code enters OAP Data front doors.

This is a narrow source guard; it is not evidence that every runtime dependency,
deployment environment or historical data transfer has been audited.
"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SURFACES = (
    ROOT / "app.py",
    ROOT / "templates" / "home.html",
    ROOT / "templates" / "world.html",
)
BLOCKED = re.compile(
    r"(?i)(?:"
    r"connect\.facebook\.net|facebook\.com/tr|"
    r"graph\.facebook\.com|graph\.instagram\.com|"
    r"api\.whatsapp\.com|wa\.me/|"
    r"fbq\s*\(|_fbp\b|_fbc\b|"
    r"facebook[-_]pixel|meta[-_]pixel|"
    r"facebook[-_]sdk|instagram[-_]sdk|whatsapp[-_]cloud[-_]api"
    r")"
)


class FirstPartyOapDataTests(unittest.TestCase):
    def test_public_data_front_doors_do_not_embed_meta_trackers(self):
        for path in SURFACES:
            with self.subTest(path=str(path.relative_to(ROOT))):
                self.assertTrue(path.is_file(), "Required first-party surface missing")
                data = path.read_text(encoding="utf-8")
                match = BLOCKED.search(data)
                self.assertIsNone(match, f"Disallowed third-party tracking/data code: {match.group() if match else ''}")

    def test_guard_detects_real_meta_sdk_examples(self):
        for example in ("https://connect.facebook.net/en_US/fbevents.js",
                        "fbq('track', 'PageView')",
                        "https://graph.facebook.com/v22.0/",
                        "https://api.whatsapp.com/send"):
            self.assertIsNotNone(BLOCKED.search(example))


if __name__ == "__main__":
    unittest.main()
