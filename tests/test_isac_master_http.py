"""Founder-only ISAC master HTTP boundary, using the real Flask test client."""


def test_master_status_requires_authenticated_founder(anonymous_client):
    response = anonymous_client.get("/mission/isac-spatial/app/master-status")
    assert response.status_code in (401, 403)
    assert response.get_json() is not None
    assert response.headers.get("Cache-Control") == "no-store"
    assert response.headers.get("X-Content-Type-Options") == "nosniff"


def test_master_status_founder_response_is_uncached_and_fail_closed(client):
    response = client.get("/mission/isac-spatial/app/master-status")
    assert response.status_code == 200
    assert response.headers.get("Cache-Control") == "no-store"
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    payload = response.get_json()
    assert payload["scope"] == "FOUNDER_PRIVATE"
    assert payload["founder_final"] is True
    assert payload["gorilla"]["physical_actions_authorized"] is False
    assert payload["continuous_monitoring_verified"] is False
    assert payload["incoming"]["world_crisis"]["status"] == "NOT_CONNECTED"
    assert payload["intelligence"]["human_rights"]["status"] == "NOT_CONNECTED"
