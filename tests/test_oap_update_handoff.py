"""OAP manual update must remain Android-approved, first-party and non-destructive."""
import unittest
from pathlib import Path

SOURCE = Path("android/oaphome/src/main/java/com/onanypostcode/oaphome/MainActivity.java")


class OapUpdateHandoffTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = SOURCE.read_text()

    def test_android_picker_and_package_installer(self):
        for token in (
            "Intent.ACTION_OPEN_DOCUMENT",
            "Intent.CATEGORY_OPENABLE",
            "application/vnd.android.package-archive",
            "Intent.ACTION_VIEW",
            "Intent.FLAG_GRANT_READ_URI_PERMISSION",
            "onActivityResult(int requestCode, int resultCode, Intent data)",
            '"content".equals(apk.getScheme())',
            "CHOOSE DOWNLOADED APK · UPDATE OAP CORE",
            "♻ UPDATE OAP CORE · CHOOSE APK",
            "⚙ OAP UPDATE PREFERENCES",
        ):
            self.assertIn(token, self.source)

    def test_existing_preferences_remain(self):
        for token in ('"automatic"', '"wifi_large"', '"prefer_idle"', '"notify"'):
            self.assertIn(token, self.source)


if __name__ == "__main__":
    unittest.main()
