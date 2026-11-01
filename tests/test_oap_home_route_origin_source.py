"""Source contract: OAP launcher must not silently redirect routes to an obsolete public site."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "android/oaphome/src/main/java/com/onanypostcode/oaphome/MainActivity.java"


def test_routes_fail_closed_without_configured_origin():
    java = SOURCE.read_text(encoding="utf-8")
    assert 'private static final String OAP_ORIGIN_PREF' in java
    assert 'private String verifiedOapOrigin()' in java
    assert 'showUnconfiguredOapRoute(name);' in java
    assert 'openInternetAddress(origin + path);' in java
    assert 'https://www.onanypostcode.com' not in java
    assert 'getPreferences(MODE_PRIVATE).edit().remove(OAP_ORIGIN_PREF)' in java


def test_https_only_for_configured_webview_origin():
    java = SOURCE.read_text(encoding="utf-8")
    assert 'safeWebAddress(parsed)' in java
    assert 'candidate.equals("https://" + parsed.getHost())' in java
    assert 'A local HTTP service is not supported by this secure WebView build.' in java
