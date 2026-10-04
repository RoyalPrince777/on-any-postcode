from pathlib import Path

SOURCE = Path("android/oapworld/src/main/java/com/onanypostcode/oapworld/MainActivity.java")


def test_oap_browser_keeps_oap_as_home_and_routes_search_first_party():
    source = SOURCE.read_text(encoding="utf-8")
    assert 'private static final String OAP_ORIGIN = "https://on-any-postcode.onrender.com"' in source
    assert 'webView.loadUrl(OAP_ORIGIN + "/")' in source
    assert 'webView.loadUrl(OAP_ORIGIN + "/search?q=" + Uri.encode(input))' in source


def test_oap_browser_opens_direct_web_addresses_without_accepting_arbitrary_schemes():
    source = SOURCE.read_text(encoding="utf-8")
    assert '"https".equalsIgnoreCase(scheme) || "http".equalsIgnoreCase(scheme)' in source
    assert 'webView.loadUrl("https://" + input)' in source
    assert 'return !("https".equalsIgnoreCase(scheme) || "http".equalsIgnoreCase(scheme));' in source


def test_oap_browser_retains_host_security_controls():
    source = SOURCE.read_text(encoding="utf-8")
    assert "settings.setAllowFileAccess(false)" in source
    assert "settings.setAllowContentAccess(false)" in source
    assert "settings.setMixedContentMode(WebSettings.MIXED_CONTENT_NEVER_ALLOW)" in source
    assert "settings.setSafeBrowsingEnabled(true)" in source
    assert "settings.setGeolocationEnabled(false)" in source
    assert "cookieManager.setAcceptThirdPartyCookies(webView, false)" in source


def test_oap_browser_has_real_navigation_controls():
    source = SOURCE.read_text(encoding="utf-8")
    for marker in (
        'navButton("‹")',
        'navButton("›")',
        'navButton("OAP")',
        'navButton("↻")',
        'navButton("Go")',
        "webView.goBack()",
        "webView.goForward()",
        "webView.reload()",
    ):
        assert marker in source
