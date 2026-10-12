"""Founder-approved browser name must not silently rebrand the OAP OS install shell."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_world_displays_browser_identity_without_fake_launch():
    html = (ROOT / "templates/world.html").read_text(encoding="utf-8")
    assert "<strong>🌐 BEGORO-KORADASO Internet</strong>" in html
    assert "The Android browser remains a separate application" in html
    assert 'id="world-query"' in html
    assert "OPEN WEB" in html


def test_browser_identity_does_not_rename_os_manifest():
    import json

    manifest = json.loads((ROOT / "static/manifest.webmanifest").read_text(encoding="utf-8"))
    assert manifest["short_name"] == "OAP OS"
    assert manifest["start_url"].startswith("/world")


def test_android_launcher_label_is_koradaso_without_permission_changes():
    import xml.etree.ElementTree as ET

    root = ET.fromstring((ROOT / "android/oapworld/src/main/AndroidManifest.xml").read_text(encoding="utf-8"))
    android = "{http://schemas.android.com/apk/res/android}"
    application = root.find("application")
    assert application is not None
    assert application.attrib[android + "label"] == "BEGORO-KORADASO"
    permissions = [element.attrib[android + "name"] for element in root.findall("uses-permission")]
    assert permissions == ["android.permission.INTERNET"]
