from pathlib import Path

SOURCE = Path("android/oapworld/src/main/java/com/onanypostcode/oapworld/MainActivity.java")


def test_oap_browser_keeps_oap_as_home_and_routes_search_first_party():
    source = SOURCE.read_text(encoding="utf-8")
    assert 'private static final String OAP_ORIGIN = "https://on-any-postcode.onrender.com"' in source
    assert 'private static final String OAP_WORLD_PATH = "/world"' in source
    assert 'openFirstPartyPath(OAP_WORLD_PATH)' in source
    assert 'openFirstPartyPath("/search?q=" + Uri.encode(input))' in source


def test_oap_browser_opens_direct_web_addresses_without_accepting_arbitrary_schemes():
    source = SOURCE.read_text(encoding="utf-8")
    assert '"https".equalsIgnoreCase(scheme) || "http".equalsIgnoreCase(scheme)' in source
    assert 'loadWebViewUrl("https://" + input)' in source
    assert 'return !("https".equalsIgnoreCase(scheme) || "http".equalsIgnoreCase(scheme));' in source


def test_oap_browser_retains_host_security_controls():
    source = SOURCE.read_text(encoding="utf-8")
    assert "settings.setAllowFileAccess(false)" in source
    assert "settings.setAllowContentAccess(false)" in source
    assert "settings.setMixedContentMode(WebSettings.MIXED_CONTENT_NEVER_ALLOW)" in source
    assert "settings.setSafeBrowsingEnabled(true)" in source
    assert "settings.setGeolocationEnabled(false)" in source
    assert "cookieManager.setAcceptThirdPartyCookies(webView, false)" in source


def test_oap_browser_shell_is_stripped_to_world_back_omnibox_and_trust_state():
    source = SOURCE.read_text(encoding="utf-8")
    for marker in (
        'navButton("‹")',
        'navButton("OAP World")',
        'trustState.setText("OAP WORLD")',
        '"OPEN WEB"',
        "webView.goBack()",
    ):
        assert marker in source
    for noise in (
        'navButton("›")',
        'navButton("↻")',
        'navButton("Go")',
        "forwardButton",
        "webView.goForward()",
        "webView.reload()",
    ):
        assert noise not in source



def test_oap_android_has_native_engine_surface_and_explicit_webview_fallback():
    source = SOURCE.read_text(encoding="utf-8")
    assert "private OapEngineView engineView;" in source
    assert "void showOapEngineDocument(String displayListJson, String sourcePath)" in source
    assert "engineView.setDisplayListJson(displayListJson)" in source
    assert "private void showWebViewFallback()" in source
    assert "engineNativeHost.setVisibility(View.VISIBLE)" in source
    assert "engineNativeHost.setVisibility(View.GONE)" in source
    assert "webView.setVisibility(View.GONE)" in source
    assert "webView.setVisibility(View.VISIBLE)" in source


def test_oap_android_engine_bridge_does_not_use_javascript_interface():
    source = SOURCE.read_text(encoding="utf-8")
    engine_view = Path(
        "android/oapworld/src/main/java/com/onanypostcode/oapworld/OapEngineView.java"
    ).read_text(encoding="utf-8")
    assert "addJavascriptInterface" not in source
    assert "addJavascriptInterface" not in engine_view
    assert '"https".equalsIgnoreCase(scheme) || "http".equalsIgnoreCase(scheme)' in engine_view


def test_oap_engine_display_list_contract_is_versioned_for_android():
    from oap.browser_engine import render_html

    document = render_html("<p>Native OAP Engine</p>", viewport_width=320).to_dict()
    assert document["engine"] == "OAP_ENGINE"
    assert document["contract_version"] == 1
    assert document["width"] == 320
    assert document["items"][0]["text"] == "Native OAP Engine"



def test_oap_browser_routes_same_origin_pages_native_first_and_external_web_to_webview():
    source = SOURCE.read_text(encoding="utf-8")
    assert "private void openFirstPartyPath(String sourcePath)" in source
    assert "engineClient.fetch(path, viewportWidth" in source
    assert 'loadWebViewUrl("https://" + input)' in source
    assert "if (sameOrigin)" in source
    assert 'openFirstPartyPath(query == null ? path : path + "?" + query)' in source


def test_oap_browser_engine_transport_is_background_bounded_and_same_origin():
    client_source = Path(
        "android/oapworld/src/main/java/com/onanypostcode/oapworld/EngineDocumentClient.java"
    ).read_text(encoding="utf-8")
    assert "Executors.newSingleThreadExecutor()" in client_source
    assert '"/api/oap-engine/document?path="' in client_source
    assert "setConnectTimeout(CONNECT_TIMEOUT_MS)" in client_source
    assert "setReadTimeout(READ_TIMEOUT_MS)" in client_source
    assert "MAX_DOCUMENT_BYTES" in client_source
    assert '"OAP_ENGINE".equals(renderer)' in client_source


def test_oap_browser_trust_state_is_origin_based_not_renderer_based():
    source = SOURCE.read_text(encoding="utf-8")
    assert "private boolean isOapUrl(String rawUrl)" in source
    assert 'trustState.setText(isOapUrl(rawUrl) ? "OAP WORLD" : "OPEN WEB")' in source


def test_oap_browser_has_no_duplicate_native_search_bar_or_tab_surface():
    source = SOURCE.read_text(encoding="utf-8")
    assert "engineFormBar" not in source
    assert "engineSearchButton" not in source
    assert "engineSearchInput" not in source
    assert "TabLayout" not in source
    assert "tabs" not in source.lower()
