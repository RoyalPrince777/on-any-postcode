from __future__ import annotations

import app as app_module
from mission_control import config


def test_healthz_is_read_only_redacted_and_fail_closed(client, tmp_path, monkeypatch):
    database_path = tmp_path / "healthz.db"
    monkeypatch.setattr(config, "OAP_DATABASE_PATH", str(database_path))

    response = client.get("/healthz")
    payload = response.get_json()

    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    assert payload == {"status": "unavailable"}
    assert not database_path.exists()
    assert client.post("/healthz").status_code == 405


def test_livez_returns_only_the_coarse_liveness_state(client):
    response = client.get("/livez")

    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    assert response.get_json() == {"status": "alive"}


def test_security_headers_are_applied_to_public_and_mission_routes(client):
    for path in ("/", "/healthz", "/mission/", "/mission/agents"):
        response = client.get(path)
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert response.headers["X-Frame-Options"] == "DENY"
        assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
        assert response.headers["Permissions-Policy"] == (
            "camera=(self), microphone=(self), geolocation=(), payment=()"
        )
        assert "default-src 'self'" in response.headers["Content-Security-Policy"]
        assert response.headers["X-OAP-Request-ID"]


def test_public_local_records_are_bounded_and_input_is_truncated(
    client, csrf, monkeypatch
):
    app_module.signal_posts.clear()
    monkeypatch.setattr(
        app_module.web_security.PUBLIC_WRITE_LIMITER, "allow", lambda _key: True
    )
    for index in range(app_module.MAX_PUBLIC_RECORDS + 5):
        response = client.post(
            "/signal",
            data={
                **csrf,
                "name": "N" * 200,
                "body": f"{index}-" + "B" * 3000,
            },
        )
        assert response.status_code == 302

    assert len(app_module.signal_posts) == app_module.MAX_PUBLIC_RECORDS
    assert len(app_module.signal_posts[0]["name"]) == 80
    assert len(app_module.signal_posts[0]["body"]) == 2000


def test_public_writes_require_csrf(client):
    response = client.post("/signal", data={"name": "Neo", "body": "Signal"})

    assert response.status_code == 403
    assert response.get_json()["error"]["code"] == "csrf_failed"
    assert app_module.signal_posts == []
