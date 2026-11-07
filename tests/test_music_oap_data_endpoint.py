"""HTTP contract tests for OAP Data's fail-closed public endpoint."""

from flask import Flask

from mission_control import music_oap_data_schema, music_public_views


def _client():
    app = Flask(__name__)
    app.register_blueprint(music_public_views.bp)
    return app.test_client()


def test_data_endpoint_returns_only_discovery_projection(monkeypatch):
    observed = {}

    def discover(**kwargs):
        observed.update(kwargs)
        return [{"track_id": "safe", "country": None, "playback_enabled": False}]

    monkeypatch.setattr(music_oap_data_schema, "discover_public_data", discover)
    response = _client().get("/music/api/data?country=GH&genre=Highlife")
    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.json["public_metadata_only"] is True
    assert response.json["playback_enabled"] is False
    assert response.json["items"][0]["country"] is None
    assert observed == {"genre": "Highlife", "language": None, "country": "GH", "limit": 50}


def test_data_endpoint_invalid_filter_does_not_expose_internal_details(monkeypatch):
    def invalid(**kwargs):
        raise ValueError("internal validation details")

    monkeypatch.setattr(music_oap_data_schema, "discover_public_data", invalid)
    response = _client().get("/music/api/data?country=GHA")
    assert response.status_code == 400
    assert response.json == {"error": "invalid_metadata_filter"}
    assert "internal" not in response.get_data(as_text=True)
    assert response.headers["Cache-Control"] == "no-store"


def test_data_endpoint_store_failure_is_fail_closed(monkeypatch):
    def unavailable(**kwargs):
        raise RuntimeError("sensitive database error")

    monkeypatch.setattr(music_oap_data_schema, "discover_public_data", unavailable)
    response = _client().get("/music/api/data")
    assert response.status_code == 503
    assert response.json["items"] == []
    assert response.json["playback_enabled"] is False
    assert response.json["temporarily_unavailable"] is True
    assert "sensitive" not in response.get_data(as_text=True)
    assert response.headers["Cache-Control"] == "no-store"
