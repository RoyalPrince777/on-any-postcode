import pytest

from oap.browser_engine.cache import ResponseCache
from oap.browser_engine.first_party_fetch import (
    canonical_first_party_target,
    fetch_first_party,
)


def test_first_party_target_is_relative_certified_and_query_bounded():
    assert canonical_first_party_target("/") == "/"
    assert canonical_first_party_target("/search?q=music") == "/search?q=music"
    with pytest.raises(ValueError, match="first_party_target_must_be_relative"):
        canonical_first_party_target("https://evil.example/")
    with pytest.raises(ValueError, match="uncertified_first_party_target"):
        canonical_first_party_target("/mission/ollama")


def test_first_party_fetch_reads_public_oap_route_and_uses_cache(client, app):
    cache = ResponseCache()
    first = fetch_first_party(app, "/search?q=music", cache=cache)
    assert first.status_code == 200
    assert "text/html" in first.content_type
    assert first.from_cache is False

    second = fetch_first_party(app, "/search?q=music", cache=cache)
    assert second.status_code == 200
    assert second.body == first.body
    assert second.from_cache is True


def test_first_party_fetch_rejects_write_methods(app):
    with pytest.raises(ValueError, match="unsupported_first_party_fetch_method"):
        fetch_first_party(app, "/search", method="POST")


def test_native_engine_document_still_uses_versioned_contract_via_fetch_pipeline(client):
    response = client.get(
        "/api/oap-engine/document",
        query_string={"path": "/search?q=music", "viewport": "320"},
    )
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["engine"] == "OAP_ENGINE"
    assert payload["contract_version"] == 1
    assert payload["source_path"] == "/search?q=music"
    assert payload["routing"] == "OAP_ENGINE_NATIVE"
