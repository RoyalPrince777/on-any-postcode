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
