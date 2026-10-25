"""Source contract for the bounded native OAP Home V2 → Founder SMI launch.

This checks launcher wiring only, not Android installation, login or HTTPS reachability.
"""
from pathlib import Path

SOURCE = Path("android/oaphome/src/main/java/com/onanypostcode/oaphome/MainActivity.java")
MANIFEST = Path("android/oaphome/src/main/AndroidManifest.xml")


def test_v2_home_exposes_single_explicit_private_smi_entry():
    java = SOURCE.read_text(encoding="utf-8")
    assert java.count("Button smiQuick = button(") == 1
    assert "🧠 SMI · CAPTAIN ALL IN" in java
    assert "FOUNDER SIGN-IN REQUIRED" in java
    assert 'v -> openSmi()' in java
    assert java.count("private void openSmi()") == 1
    assert 'SMI_FOUNDER_PATH = "/mission/smi"' in java
    assert '"SMI".equals(normalized)' in java
    assert '"CAPTAIN ALL IN".equals(normalized)' in java
    assert '"SOVEREIGN MEGAVERSE INTELLIGENCE".equals(normalized)' in java
    assert 'if ("SMI".equals(name))' in java


def test_smi_launch_is_system_browser_handoff_without_native_identity_or_media():
    java = SOURCE.read_text(encoding="utf-8")
    start = java.index("    private void openSmi() {")
    end = java.index("    private void openPttApp() {", start)
    handoff = java[start:end]

    assert "Uri.parse(OAP_API_ORIGIN + SMI_FOUNDER_PATH)" in handoff
    assert "safeWebAddress(uri)" in handoff
    assert "Intent.ACTION_VIEW" in handoff
    assert "Intent.CATEGORY_BROWSABLE" in handoff
    assert "startActivity(smi)" in handoff
    assert "ActivityNotFoundException" in handoff

    for forbidden in (
        "setJavaScriptEnabled(true)", "WebView(", "CookieManager",
        "getCookie(", "putExtra(", "Authorization", "csrf", "camera",
        "getUserMedia", "getSharedPreferences", "setDataAndType",
    ):
        assert forbidden not in handoff

    assert "settings.setJavaScriptEnabled(false)" in java
    assert "com.onanypostcode.oaphome.v2" not in handoff
    assert "android.permission.CAMERA" not in MANIFEST.read_text(encoding="utf-8")


def test_v2_does_not_confuse_launcher_wiring_with_live_smi_verification():
    java = SOURCE.read_text(encoding="utf-8")
    assert 'OAP_API_ORIGIN = "https://www.onanypostcode.com"' in java
    assert "FOUNDER SIGN-IN REQUIRED" in java
    assert "A compatible Android browser is required for private SMI" in java
    assert "OAP_SMI_FACE_DETECTION_ENABLED" not in java
    assert "oap_home_smi_private_token" not in java
