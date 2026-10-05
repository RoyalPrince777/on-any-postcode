import pytest

from oap.browser_engine.submit import build_certified_get_target


def test_certified_get_submission_builds_search_target():
    assert build_certified_get_target(
        "/search",
        {"q": "music", "category": "Media"},
    ) == "/search?q=music&category=Media"


def test_certified_get_submission_rejects_arbitrary_origins_and_actions():
    with pytest.raises(ValueError, match="form_action_must_be_first_party_path"):
        build_certified_get_target("https://evil.example/search", {"q": "x"})
    with pytest.raises(ValueError, match="unsupported_form_action"):
        build_certified_get_target("/market", {"q": "x"})
    with pytest.raises(ValueError, match="form_action_query_not_allowed"):
        build_certified_get_target("/search?x=1", {"q": "x"})


def test_certified_get_submission_rejects_secret_fields_and_oversized_values():
    with pytest.raises(ValueError, match="sensitive_form_field_not_allowed"):
        build_certified_get_target("/search", {"password": "secret"})
    with pytest.raises(ValueError, match="form_field_value_too_large"):
        build_certified_get_target("/search", {"q": "x" * 4097})


def test_form_submission_endpoint_returns_fresh_engine_document(client):
    response = client.post(
        "/api/oap-engine/submit",
        json={
            "action": "/search",
            "fields": {"q": "music"},
            "viewport": 320,
        },
    )
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["engine"] == "OAP_ENGINE"
    assert payload["contract_version"] == 1
    assert payload["source_path"] == "/search?q=music"
    assert payload["submission"] == {
        "method": "GET",
        "certified": True,
        "action": "/search",
    }
    assert response.headers["X-OAP-Renderer"] == "OAP_ENGINE"
    assert response.headers["Cache-Control"] == "no-store"


def test_form_submission_endpoint_rejects_unsupported_action(client):
    response = client.post(
        "/api/oap-engine/submit",
        json={"action": "/market", "fields": {"q": "music"}},
    )
    assert response.status_code == 400
    assert response.get_json()["error"] == "unsupported_form_action"
