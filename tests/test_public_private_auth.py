from __future__ import annotations

import app as app_module
from mission_control import neon_auth, public_store, web_security

AUTH_ID = "11111111-1111-4111-8111-111111111111"


def test_public_world_and_product_surfaces_remain_anonymous(anonymous_client):
    for path in (
        "/",
        "/world",
        "/healthz",
        "/mission/status",
        "/mission/chat/status",
        "/mission/spot",
        "/mission/the-link",
        "/mission/linkup",
    ):
        assert anonymous_client.get(path).status_code == 200

    assert anonymous_client.get("/the-spot").status_code == 302
    assert anonymous_client.get("/the-link").status_code == 302
    assert anonymous_client.get("/linkup").status_code == 302


def test_private_html_surfaces_redirect_anonymous_visitors(anonymous_client):
    for path in (
        "/my-world",
        "/myworld",
        "/mission",
        "/mission/agents",
        "/mission/brain",
        "/mission/ollama",
        "/mission/infrastructure",
        "/mission/organism",
        "/infrastructure",
    ):
        response = anonymous_client.get(path)
        assert response.status_code == 302
        assert "/enter-my-world?next=" in response.headers["Location"]


def test_private_apis_fail_closed_with_structured_401(anonymous_client):
    for path in (
        "/mission/brain/status",
        "/mission/conversations",
        "/infrastructure/services",
        "/api/infrastructure/status",
    ):
        response = anonymous_client.get(path)
        assert response.status_code == 401
        assert response.get_json()["error"]["code"] == "authentication_required"
        assert response.headers["Cache-Control"] == "no-store"

    chat = anonymous_client.post("/mission/chat", json={"message": "private"})
    assert chat.status_code == 401
    assert chat.get_json()["error"]["code"] == "authentication_required"


def test_public_home_never_renders_private_profile_records(client):
    app_module.profiles[AUTH_ID] = {
        "nickname": "PRIVATE PROFILE VALUE",
        "country": "PRIVATE COUNTRY VALUE",
    }

    page = client.get("/").get_data(as_text=True)

    assert "PRIVATE PROFILE VALUE" not in page
    assert "PRIVATE COUNTRY VALUE" not in page
    assert 'method="post" action="/myworld"' not in page


def test_my_world_reads_only_verified_uuid_owner(client, monkeypatch):
    observed = {}
    monkeypatch.setattr(public_store, "status", lambda: {"configured": True})

    def fake_sync(identity_id, *, email, display_name):
        observed["sync"] = (identity_id, email, display_name)

    def fake_get(identity_id):
        observed["read"] = identity_id
        return {"nickname": "Private Neo", "country": "Ghana"}

    monkeypatch.setattr(public_store, "ensure_authenticated_user", fake_sync)
    monkeypatch.setattr(public_store, "get_profile", fake_get)

    response = client.get("/my-world")
    page = response.get_data(as_text=True)

    assert response.status_code == 200
    assert observed == {
        "sync": (AUTH_ID, "member@example.test", "OAP Member"),
        "read": AUTH_ID,
    }
    assert "Private Neo" in page
    assert "Ghana" in page


def test_my_world_update_uses_verified_uuid_owner(client, csrf, monkeypatch):
    observed = {}
    monkeypatch.setattr(public_store, "status", lambda: {"configured": True})
    monkeypatch.setattr(public_store, "ensure_authenticated_user", lambda *a, **k: None)

    def fake_update(identity_id, *, nickname, country):
        observed["update"] = (identity_id, nickname, country)

    monkeypatch.setattr(public_store, "update_profile", fake_update)

    response = client.post(
        "/myworld",
        data={**csrf, "nickname": "Owner", "country": "Ghana"},
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/my-world")
    assert observed["update"] == (AUTH_ID, "Owner", "Ghana")


def test_anonymous_profile_write_cannot_cross_private_boundary(anonymous_client):
    token = "anonymous-private-csrf-token-value-123456"
    with anonymous_client.session_transaction() as current_session:
        current_session[web_security.CSRF_SESSION_KEY] = token

    response = anonymous_client.post(
        "/myworld",
        data={"csrf_token": token, "nickname": "Intruder", "country": "Nowhere"},
    )

    assert response.status_code == 302
    assert "/enter-my-world?next=" in response.headers["Location"]
    assert app_module.profiles == {}


def test_sign_in_bridges_opaque_cookie_and_rejects_external_next(
    anonymous_client, monkeypatch
):
    token = "auth-form-csrf-token-value-1234567890"
    with anonymous_client.session_transaction() as current_session:
        current_session[web_security.CSRF_SESSION_KEY] = token
    observed = {}

    def fake_sign_in(email, password):
        observed["credentials"] = (email, password)
        return neon_auth.AuthResult(
            status_code=200,
            payload={"user": {"id": AUTH_ID}},
            set_cookie_headers=(
                (
                    "better-auth.session_token=opaque-value; "
                    "Domain=example.neonauth.test; Path=/neondb/auth; "
                    "Secure; HttpOnly; SameSite=None; Max-Age=2592000"
                ),
            ),
        )

    monkeypatch.setattr(neon_auth, "sign_in", fake_sign_in)
    response = anonymous_client.post(
        "/auth/sign-in",
        data={
            "csrf_token": token,
            "email": "MEMBER@EXAMPLE.TEST",
            "password": "  secret pass  ",
            "next": "//evil.example/private",
        },
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/my-world")
    assert observed["credentials"] == (
        "member@example.test",
        "  secret pass  ",
    )
    auth_cookie = next(
        value
        for value in response.headers.getlist("Set-Cookie")
        if value.startswith("better-auth.session_token=")
    )
    assert "Domain=" not in auth_cookie
    assert "Path=/; Secure; HttpOnly; SameSite=Lax" in auth_cookie
    with anonymous_client.session_transaction() as current_session:
        assert current_session[neon_auth.AUTH_COOKIE_NAMES_SESSION_KEY] == [
            "better-auth.session_token"
        ]


def test_sign_out_forwards_only_auth_cookie_and_clears_session(
    client, csrf, monkeypatch
):
    observed = {}

    def fake_sign_out(cookie_header):
        observed["cookie"] = cookie_header
        return neon_auth.AuthResult(status_code=200, payload={"success": True})

    monkeypatch.setattr(neon_auth, "sign_out", fake_sign_out)
    response = client.post("/auth/sign-out", data=csrf)

    assert response.status_code == 302
    assert observed["cookie"] == (
        "better-auth.session_token=verified-test-session"
    )
    assert "session=" not in observed["cookie"]
    assert any(
        header.startswith("better-auth.session_token=;") and "Max-Age=0" in header
        for header in response.headers.getlist("Set-Cookie")
    )
    assert client.get("/my-world").status_code == 302
