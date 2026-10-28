"""Static contracts for native OAP Home V2; Android compilation is a separate gate."""
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NATIVE = ROOT / "android" / "oaphome"
JAVA = NATIVE / "src/main/java/com/onanypostcode/oaphome/MainActivity.java"
ART = NATIVE / "src/main/java/com/onanypostcode/oaphome/RoyalHomeArt.java"
MANIFEST = NATIVE / "src/main/AndroidManifest.xml"
GRADLE = NATIVE / "build.gradle"
ANDROID = "{http://schemas.android.com/apk/res/android}"


class NativeRoyalHomeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = JAVA.read_text(encoding="utf-8")
        cls.art = ART.read_text(encoding="utf-8")
        cls.manifest = ET.parse(MANIFEST).getroot()

    def test_android_launcher_is_selectable_not_forced(self):
        app = self.manifest.find("application")
        self.assertEqual(app.get(ANDROID + "label"), "OAP Home")
        activity = app.find("activity")
        self.assertEqual(activity.get(ANDROID + "exported"), "true")
        filters = activity.findall("intent-filter")
        self.assertTrue(any(
            {x.get(ANDROID + "name") for x in item.findall("category")}
            >= {"android.intent.category.HOME", "android.intent.category.DEFAULT"}
            for item in filters
        ))
        self.assertNotIn("BIND_DEVICE_ADMIN", MANIFEST.read_text(encoding="utf-8"))
        self.assertIn("Settings.ACTION_HOME_SETTINGS", self.source)
        self.assertEqual(len(self.manifest.find("application").findall("activity")), 1)

    def test_package_identity_and_separate_internet_app(self):
        build = GRADLE.read_text(encoding="utf-8")
        self.assertIn("applicationId 'com.onanypostcode.oaphome.v2'", build)
        self.assertIn("versionCode 21", build)
        self.assertNotIn("applicationId 'com.onanypostcode.oaphome'\n", build)
        self.assertIn("versionName '2.1.0-founder-royal'", build)
        queries = self.manifest.find("queries")
        self.assertIsNotNone(queries)
        self.assertTrue(any(p.get(ANDROID + "name") == "com.onanypostcode.oapworld"
                            for p in queries.findall("package")))
        self.assertIn('OAP_INTERNET_PACKAGE = "com.onanypostcode.oapworld"', self.source)
        self.assertIn("getLaunchIntentForPackage(OAP_INTERNET_PACKAGE)", self.source)
        self.assertIn("else if (index == 2) launchOapInternet();", self.source)
        self.assertIn("No browser fallback or installation is started.", self.source)
        self.assertIn("KORADASO Internet is separate", self.source)
        self.assertIn("The KORADASO Internet Android app is not installed or visible.", self.source)
        self.assertIn("KORADASO Internet could not be opened.", self.source)
        self.assertIn("OPEN KORADASO INTERNET", self.source)

    def test_home_draws_native_royal_surface_not_html(self):
        self.assertIn("new RoyalHomeArt.EarthBackdrop()", self.source)
        self.assertIn("new RoyalHomeArt.TileDrawable(i)", self.source)
        self.assertIn("android.graphics.Canvas", self.art)
        self.assertIn("static final class EarthBackdrop", self.art)
        self.assertIn("static final class TileDrawable", self.art)
        self.assertIn("FrameLayout royalHero", self.source)
        self.assertIn('base("♛ OAP HOME")', self.source)
        home = self.source.split("    private void home() {", 1)[1].split(
            "    private void addPersistentHomeDock", 1)[0]
        self.assertNotIn("new android.webkit.WebView", home)
        self.assertNotIn("loadUrl(", home)
        self.assertEqual(home.count("String[] captions"), 1)
        self.assertIn("LINK UP", home)
        self.assertIn("OAP LIBRARY", home)
        self.assertIn("OAP STORE", home)
        self.assertIn("STANDALONE · MIC OFF", home)

    def test_clocks_are_real_and_weather_calendar_not_fabricated(self):
        for timezone in (
            "Europe/London", "America/New_York", "Asia/Dubai", "Africa/Accra"
        ):
            self.assertIn(timezone, self.source)
        self.assertIn('new java.text.SimpleDateFormat("HH:mm"', self.source)
        self.assertIn("clockHandler.postDelayed(clockTick, 60000)", self.source)
        self.assertIn("NOT CONNECTED", self.source)
        self.assertNotIn("Mostly Sunny", self.source)

    def test_royal_tiles_adapt_without_changing_routes(self):
        home = self.source.split("    private void home() {", 1)[1].split(
            "    private void addPersistentHomeDock", 1)[0]
        self.assertIn("int columns = availableWidth < dp(336) ? 2 : 3;", home)
        self.assertIn("grid.setColumnCount(columns)", home)
        self.assertIn("(availableWidth - dp(4 * columns)) / columns", home)
        self.assertIn("tile.setAllCaps(false)", home)
        self.assertIn("v -> destination(name)", home)
        self.assertIn("new RoyalHomeArt.TileDrawable(i)", home)

    def test_autoupdate_preferences_are_local_and_do_not_install(self):
        source = self.source
        self.assertIn('getSharedPreferences("oap_autoupdate_preferences_v1", MODE_PRIVATE)', source)
        self.assertIn('addButton("♻ OAP AUTOUPDATE PREFERENCES", v -> autoUpdatePreferences())', source)
        self.assertIn('"automatic", true', source)
        self.assertIn('"wifi_large", true', source)
        self.assertIn('"prefer_idle", true', source)
        self.assertIn('"notify", true', source)
        self.assertIn("UPDATE ENGINE NOT CONNECTED", source)
        block = source.split("private void autoUpdatePreferences() {", 1)[1].split(
            "    private void allApps()", 1
        )[0]
        for disallowed in ("PackageInstaller", "ACTION_INSTALL_PACKAGE", "DownloadManager",
                           "HttpURLConnection", "startActivityForResult"):
            self.assertNotIn(disallowed, block)

    def test_no_silent_install_or_os_replace(self):
        manifest = MANIFEST.read_text(encoding="utf-8")
        self.assertNotIn("DEVICE_OWNER", manifest)
        self.assertNotIn("REBOOT", manifest)
        self.assertNotIn("WRITE_SECURE_SETTINGS", manifest)
        self.assertNotIn("startLockTask", self.source)
        self.assertNotIn("pm uninstall", self.source)
        self.assertNotIn("setPreferredActivity", self.source)
        self.assertIn("getPackageManager().queryIntentActivities", self.source)


if __name__ == "__main__":
    unittest.main()
