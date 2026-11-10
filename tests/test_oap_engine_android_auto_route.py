from oap.browser_engine.android_route import canonical_supported_target


def test_oap_engine_android_target_allowlist_is_fail_closed():
    assert canonical_supported_target("/") == "/world"
    assert canonical_supported_target("/world") == "/world"
    assert canonical_supported_target("/search") == "/search"
    assert canonical_supported_target("/search?q=music") == "/search?q=music"
    assert canonical_supported_target("/market") is None
    assert canonical_supported_target("/mission/ollama") is None
    assert canonical_supported_target("https://example.com/") is None
    assert canonical_supported_target("//example.com/") is None
    assert canonical_supported_target("/search?next=/mission") is None


def test_oap_engine_android_document_endpoint_renders_supported_public_search(client):
    response = client.get(
        "/api/oap-engine/document",
        query_string={"path": "/search?q=music", "viewport": "320"},
    )
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["engine"] == "OAP_ENGINE"
    assert payload["contract_version"] == 1
    assert payload["routing"] == "OAP_ENGINE_NATIVE"
    assert payload["source_path"] == "/search?q=music"
    assert payload["width"] == 320
    assert isinstance(payload["items"], list)
    assert response.headers["X-OAP-Renderer"] == "OAP_ENGINE"
    assert response.headers["Cache-Control"] == "no-store"


def test_oap_engine_android_document_endpoint_rejects_unsupported_page(client):
    response = client.get(
        "/api/oap-engine/document",
        query_string={"path": "/market", "viewport": "390"},
    )
    assert response.status_code == 404
    payload = response.get_json()
    assert payload["fallback"] == "WEBVIEW"


def test_oap_engine_android_document_normalizes_relative_links(client):
    response = client.get(
        "/api/oap-engine/document",
        query_string={"path": "/world", "viewport": "390"},
    )
    assert response.status_code == 200
    payload = response.get_json()
    hrefs = [item.get("href") for item in payload["items"] if item.get("href")]
    assert hrefs
    assert all(href.startswith(("https://", "http://")) for href in hrefs)



def test_oap_engine_android_links_ignore_untrusted_host_header(client):
    response = client.get(
        "/api/oap-engine/document",
        query_string={"path": "/world", "viewport": "390"},
        headers={"Host": "attacker.example"},
    )
    assert response.status_code == 200
    payload = response.get_json()
    hrefs = [item.get("href") for item in payload["items"] if item.get("href")]
    assert hrefs
    assert all("attacker.example" not in href for href in hrefs)
    assert all(href.startswith("https://on-any-postcode.onrender.com/") for href in hrefs)
