from oap.browser_engine.status import status


def test_oap_engine_truth_status_keeps_unbuilt_browser_layers_red():
    payload = status()
    assert payload["engine"] == "OAP_ENGINE"
    assert payload["physical_scope_excluded"] is True
    assert payload["standards_complete"] is False
    assert payload["general_web_default_renderer"] == "Android System WebView"
    assert payload["implemented"]["android_native_surface"] is True
    assert payload["implemented"]["supported_page_auto_routing"] == (
        "/",
        "/world",
        "/search",
    )
    assert "standards_complete_javascript_vm" in payload["unbuilt"]
    assert "gpu_raster_compositor" in payload["unbuilt"]
    assert "general_webview_replacement" in payload["unbuilt"]


def test_oap_engine_status_route_is_public_read_only_and_no_store(client):
    response = client.get("/api/oap-engine/status")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["standards_complete"] is False
    assert payload["physical_scope_excluded"] is True
    assert response.headers["Cache-Control"] == "no-store"
