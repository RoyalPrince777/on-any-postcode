"""Static proof for the KORADASO Internet Android browser branding.

Android hardware installation, live hosting and external-site acceptance are separate gates.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "android/oapworld/src/main/AndroidManifest.xml"
ACTIVITY = ROOT / "android/oapworld/src/main/java/com/onanypostcode/oapworld/MainActivity.java"
ICON = ROOT / "android/oapworld/src/main/res/drawable-nodpi/koradaso_royal_icon.webp"
ANDROID = "{http://schemas.android.com/apk/res/android}"
ICON_SHA256 = "30e19b2d561afa0aab48fdfe704313ee0a299e38e3d648da4a865378f8c3bdf3"


def test_koradaso_label_icon_permissions_and_package_identity():
    root = ET.fromstring(MANIFEST.read_text(encoding="utf-8"))
    app = root.find("application")
    assert app is not None
    assert app.attrib[ANDROID + "label"] == "KORADASO Internet"
    assert app.attrib[ANDROID + "icon"] == "@drawable/koradaso_royal_icon"
    assert app.attrib[ANDROID + "allowBackup"] == "false"
    assert app.attrib[ANDROID + "usesCleartextTraffic"] == "false"
    assert [e.attrib[ANDROID + "name"] for e in root.findall("uses-permission")] == [
        "android.permission.INTERNET",
    ]
    activity = app.find("activity")
    assert activity is not None
    assert activity.attrib[ANDROID + "name"] == ".MainActivity"

    build_gradle = (ROOT / "android/oapworld/build.gradle").read_text(encoding="utf-8")
    build_kts = (ROOT / "android/oapworld/build.gradle.kts").read_text(encoding="utf-8")
    assert "com.onanypostcode.oapworld" in build_gradle
    assert "com.onanypostcode.oapworld" in build_kts


def test_royal_icon_uses_approved_cropped_original_artwork():
    data = ICON.read_bytes()
    assert len(data) == 3348
    assert data[0:4] == b"RIFF"
    assert data[8:12] == b"WEBP"
    assert hashlib.sha256(data).hexdigest() == ICON_SHA256


def test_browser_ui_reuses_existing_routes_and_displays_origin_trust():
    source = ACTIVITY.read_text(encoding="utf-8")
    for marker in (
        "R.drawable.koradaso_royal_icon",
        'brandName.setText("KORADASO INTERNET")',
        'parentBrand.setText("POWERED BY ON ANY POSTCODE")',
        'royalIcon.setContentDescription("KORADASO crown and K globe emblem")',
        'navButton("OAP")',
        'openFirstPartyPath("/world")',
        'String state = firstParty ? "OAP WORLD" : "OPEN WEB"',
        '"https".equalsIgnoreCase(uri.getScheme())',
        "owned.getHost().equalsIgnoreCase(uri.getHost())",
        "uri.getUserInfo() == null",
        "uri.getPort() == -1",
        'trustLabel.setContentDescription("Trust boundary: " + state)',
    ):
        assert marker in source

    assert "addJavascriptInterface" not in source
    assert "setAcceptThirdPartyCookies(webView, false)" in source
    assert "settings.setAllowFileAccess(false)" in source
    assert "settings.setAllowContentAccess(false)" in source
    assert 'loadWebViewUrl("https://" + input)' in source


def test_oap_world_and_home_v2_not_rebranded_into_koradaso():
    world = (ROOT / "templates/world.html").read_text(encoding="utf-8")
    assert "<title>OAP World</title>" in world
    webmanifest = (ROOT / "static/manifest.webmanifest").read_text(encoding="utf-8")
    assert '"short_name": "OAP OS"' in webmanifest
    assert "android/oaphome/" not in str(ACTIVITY)
