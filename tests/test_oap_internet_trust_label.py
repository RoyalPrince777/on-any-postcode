"""Bounded source contract for Android OAP Internet trust label.

This is not Android runtime or device verification.
"""
from pathlib import Path

SOURCE = (Path(__file__).resolve().parents[1] /
          "android/oapworld/src/main/java/com/onanypostcode/oapworld/MainActivity.java").read_text()


def test_trust_label_is_part_of_existing_toolbar():
    assert "toolbar.addView(trustLabel);" in SOURCE
    assert '"OAP WORLD" : "OPEN WEB"' in SOURCE


def test_label_is_based_on_exact_https_origin_not_page_branding():
    assert '"https".equalsIgnoreCase(candidate.getScheme())' in SOURCE
    assert "trusted.getHost().equalsIgnoreCase(candidate.getHost())" in SOURCE
    assert "candidate.getPort() == -1" in SOURCE
    assert "candidate.getUserInfo() == null" in SOURCE


def test_label_updates_on_native_and_webview_navigation():
    assert "updateTrustLabel(url);" in SOURCE
    assert 'updateTrustLabel(OAP_ORIGIN + (sourcePath == null ? "/" : sourcePath));' in SOURCE
    assert "updateTrustLabel(OAP_ORIGIN + "/world");" in SOURCE
