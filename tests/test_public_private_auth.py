from __future__ import annotations

import app as app_module
from mission_control import (
    founder_activation,
    neon_auth,
    products,
    public_store,
    web_security,
)

AUTH_ID = "11111111-1111-4111-8111-111111111111"


def test_public_world_and_product_surfaces_remain_anonymous(anonymous_client):
    for path in (
        "/",
        "/world",
        "/healthz",
        "/livez",
        "/auth",
        "/the-spot",
        "/languages",
        "/world/languages",
        "/the-spot/languages",
        "/carnival",
        "/world/carnival",
        "/the-spot/carnival",
        "/the-link",
        "/linkup",
    ):
        assert anonymous_client.get(path).status_code == 200

    assert anonymous_client.get("/mission/spot").status_code == 302
    assert anonymous_client.get("/mission/the-link").status_code == 302
    assert anonymous_client.get("/mission/linkup").status_code == 302


def test_every_public_spot_capability_can_be_browsed_without_password(
    anonymous_client,
):
    for capability in products.PUBLIC_SPOT_CAPABILITIES:
        response = anonymous_client.get(f"/the-spot/{capability['slug']}")

        assert response.status_code == 200
        assert response.headers["Cache-Control"] == "no-store"


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
        "/mission/status",
        "/mission/chat/status",
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


def test_anonymous_pages_do_not_disclose_internal_architecture(anonymous_client):
    public_paths = (
        "/",
        "/world",
        "/auth",
        "/the-spot",
        "/languages",
        "/world/languages",
        "/the-spot/languages",
        "/carnival",
        "/world/carnival",
        "/the-spot/carnival",
        "/the-link",
        "/linkup",
        "/healthz",
        "/livez",
    )
    public_copy = "\n".join(
        anonymous_client.get(path).get_data(as_text=True).lower()
        for path in public_paths
    )

    for internal_term in (
        "neon",
        "postgres",
        "render.com",
        "github",
        "openai",
        "ollama",
        "sovereign megaverse intelligence",
        "smi",
        "mission control",
        "mission_control",
        "infrastructure",
        "guardian",
        "hrm",
        "agent registry",
        "provider key",
        "database",
        "schema",
        "route conflict",
        "owner conflict",
        "mutation control",
        "execution locked",
        "human authority",
    ):
        assert internal_term not in public_copy


def test_anonymous_visitors_receive_only_public_styles(anonymous_client):
    public_style = anonymous_client.get("/assets/oap.css")

    assert public_style.status_code == 200
    assert "mission-control" not in public_style.get_data(as_text=True).lower()
    assert anonymous_client.get(
        "/mission/static/mission_control.css"
    ).status_code == 404


def test_signed_in_members_can_load_private_styles(client):
    assert client.get("/mission/static/mission_control.css").status_code == 200


def _set_non_founder_session(anonymous_client, monkeypatch):
    def non_founder_session(cookie_header):
        assert "better-auth.session_token=business-session" in cookie_header
        return neon_auth.AuthResult(
            status_code=200,
            payload={
                "session": {"id": "business-session"},
                "user": {
                    "id": "22222222-2222-4222-8222-222222222222",
                    "name": "Approved Business",
                    "email": "business@example.test",
                    "emailVerified": True,
                },
            },
        )

    monkeypatch.setattr(neon_auth, "get_session", non_founder_session)
    anonymous_client.set_cookie(
        "better-auth.session_token", "business-session"
    )
    with anonymous_client.session_transaction() as current_session:
        current_session[neon_auth.AUTH_COOKIE_NAMES_SESSION_KEY] = [
            "better-auth.session_token"
        ]


def test_business_session_can_browse_public_but_cannot_open_founder_space(
    anonymous_client, monkeypatch
):
    _set_non_founder_session(anonymous_client, monkeypatch)

    assert anonymous_client.get("/the-spot/market").status_code == 200
    assert anonymous_client.get("/linkup").status_code == 200
    for path in ("/my-world", "/my-world/maps", "/infrastructure"):
        response = anonymous_client.get(path)
        assert response.status_code == 403
        assert response.get_json()["error"]["code"] == "human_authority_required"
        assert response.headers["Cache-Control"] == "no-store"
    assert anonymous_client.get(
        "/mission/static/mission_control.css"
    ).status_code == 404


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

    def fake_sync(identity_id, *, email, display_name, store_email):
        observed["sync"] = (identity_id, email, display_name, store_email)

    def fake_get(identity_id):
        observed["read"] = identity_id
        return {"nickname": "Private Neo", "country": "Ghana"}

    monkeypatch.setattr(public_store, "ensure_authenticated_user", fake_sync)
    monkeypatch.setattr(public_store, "get_profile", fake_get)

    response = client.get("/my-world")
    page = response.get_data(as_text=True)

    assert response.status_code == 200
    assert observed == {
        "sync": (AUTH_ID, "member@example.test", "OAP Member", False),
        "read": AUTH_ID,
    }
    assert "Private Neo" in page
    assert "Ghana" in page
    assert "member@example.test" not in page
    assert "Email verification" not in page


def test_my_world_update_uses_verified_uuid_owner(client, csrf, monkeypatch):
    observed = {}
    monkeypatch.setattr(public_store, "status", lambda: {"configured": True})
    monkeypatch.setattr(public_store, "ensure_authenticated_user", lambda *a, **k: None)

    def fake_update(
        identity_id, *, nickname, postcode, borough, county, country, continent
    ):
        observed["update"] = {
            "identity_id": identity_id,
            "nickname": nickname,
            "postcode": postcode,
            "borough": borough,
            "county": county,
            "country": country,
            "continent": continent,
        }

    monkeypatch.setattr(public_store, "update_profile", fake_update)

    response = client.post(
        "/myworld",
        data={**csrf, "nickname": "Owner", "country": "Ghana"},
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/my-world")
    assert observed["update"] == {
        "identity_id": AUTH_ID,
        "nickname": "Owner",
        "postcode": "",
        "borough": "",
        "county": "",
        "country": "Ghana",
        "continent": "",
    }


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


def test_private_sign_in_uses_server_selector_and_rejects_external_next(
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


def test_private_founder_sign_in_ignores_submitted_email(
    anonymous_client, monkeypatch
):
    token = "private-sign-in-csrf-token-value-1234567890"
    with anonymous_client.session_transaction() as current_session:
        current_session[web_security.CSRF_SESSION_KEY] = token

    observed = {}

    def fake_sign_in(email, password):
        observed["credentials"] = (email, password)
        return neon_auth.AuthResult(status_code=401, payload=None)

    monkeypatch.setattr(neon_auth, "sign_in", fake_sign_in)
    response = anonymous_client.post(
        "/auth/sign-in",
        data={
            "csrf_token": token,
            "email": "business@example.test",
            "password": "valid-existing-password",
            "next": "/my-world",
        },
    )

    assert response.status_code == 401
    assert observed["credentials"] == (
        "member@example.test",
        "valid-existing-password",
    )
    page = response.get_data(as_text=True)
    assert "Private password not recognised." in page
    assert 'name="email"' not in page


def test_approved_business_sign_in_is_separate_from_founder_private_gate(
    anonymous_client, monkeypatch
):
    token = "business-sign-in-csrf-token-value-123456789"
    with anonymous_client.session_transaction() as current_session:
        current_session[web_security.CSRF_SESSION_KEY] = token
    observed = {}

    def fake_sign_in(email, password):
        observed["credentials"] = (email, password)
        return neon_auth.AuthResult(
            status_code=200,
            payload={"user": {"id": "22222222-2222-4222-8222-222222222222"}},
            set_cookie_headers=(
                "better-auth.session_token=business-session; Secure; HttpOnly",
            ),
        )

    monkeypatch.setattr(neon_auth, "sign_in", fake_sign_in)
    response = anonymous_client.post(
        "/auth/sign-in",
        data={
            "csrf_token": token,
            "email": "BUSINESS@EXAMPLE.TEST",
            "password": "existing-business-password",
            "next": "/the-spot/market",
        },
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/the-spot/market")
    assert observed["credentials"] == (
        "business@example.test",
        "existing-business-password",
    )


def test_private_auth_is_password_only_and_has_no_web_signup(
    anonymous_client,
):
    founder_page = anonymous_client.get("/auth").get_data(as_text=True)
    business_page = anonymous_client.get(
        "/auth?next=/the-spot/market"
    ).get_data(as_text=True)

    assert "open to browse without an account or password" in founder_page
    assert "Private password" in founder_page
    assert 'name="email"' not in founder_page
    assert 'type="email"' not in founder_page
    assert 'action="/auth/sign-up"' not in founder_page
    assert anonymous_client.post("/auth/sign-up").status_code == 404
    assert "Public access stays free" in business_page
    assert 'name="email"' in business_page
    assert 'type="email"' in business_page
    assert 'action="/auth/sign-up"' not in business_page
    assert 'id="show-sign-in-password"' in founder_page
    assert "Show password" in founder_page


def test_one_time_founder_activation_keeps_identity_server_side(
    anonymous_client, monkeypatch
):
    activation_code = "one-time-founder-activation-code-value-123456"
    token = "founder-activation-csrf-token-value-123456"
    monkeypatch.setenv(
        founder_activation.ACTIVATION_TOKEN_ENV, activation_code
    )
    monkeypatch.setattr(founder_activation, "state", lambda: "available")
    observed = {}

    def fake_activate(password):
        observed["password"] = password
        return "activated"

    monkeypatch.setattr(founder_activation, "activate", fake_activate)
    with anonymous_client.session_transaction() as current_session:
        current_session[web_security.CSRF_SESSION_KEY] = token

    page_response = anonymous_client.get("/activate-founder")
    page = page_response.get_data(as_text=True)
    assert page_response.status_code == 200
    assert "member@example.test" not in page
    assert 'name="email"' not in page
    assert 'name="activation_code"' in page
    assert 'id="show-founder-passwords"' in page
    assert "Show both password entries" in page
    assert "between 12 and 128 characters" in page
    assert "12–21" not in page

    response = anonymous_client.post(
        "/activate-founder",
        data={
            "csrf_token": token,
            "activation_code": activation_code,
            "email": "attacker@example.test",
            "password": "  a private passphrase  ",
            "password_confirmation": "  a private passphrase  ",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert observed == {"password": "  a private passphrase  "}
    result_page = response.get_data(as_text=True)
    assert "Founder identity activated." in result_page
    assert "member@example.test" not in result_page
    assert "attacker@example.test" not in result_page


def test_founder_activation_rejects_wrong_code_before_provider_call(
    anonymous_client, monkeypatch
):
    monkeypatch.setenv(
        founder_activation.ACTIVATION_TOKEN_ENV,
        "correct-founder-activation-code-value-123456",
    )
    monkeypatch.setattr(founder_activation, "state", lambda: "available")
    token = "founder-activation-csrf-token-value-654321"
    with anonymous_client.session_transaction() as current_session:
        current_session[web_security.CSRF_SESSION_KEY] = token

    def unexpected_activate(_password):
        raise AssertionError("provider must not be called")

    monkeypatch.setattr(founder_activation, "activate", unexpected_activate)
    response = anonymous_client.post(
        "/activate-founder",
        data={
            "csrf_token": token,
            "activation_code": "wrong-code",
            "password": "a sufficiently long password",
            "password_confirmation": "a sufficiently long password",
        },
    )

    assert response.status_code == 403
    assert "not recognised" in response.get_data(as_text=True)


def test_founder_activation_fails_closed_after_first_user(
    anonymous_client, monkeypatch
):
    monkeypatch.setattr(founder_activation, "state", lambda: "complete")

    get_response = anonymous_client.get("/activate-founder")
    post_response = anonymous_client.post("/activate-founder")

    assert get_response.status_code == 404
    assert post_response.status_code == 404
    assert get_response.headers["Cache-Control"] == "no-store"


def test_founder_activation_requires_csrf_before_accepting_secrets(
    anonymous_client, monkeypatch
):
    monkeypatch.setattr(founder_activation, "state", lambda: "available")

    response = anonymous_client.post(
        "/activate-founder",
        data={
            "activation_code": "not-evaluated",
            "password": "a sufficiently long password",
            "password_confirmation": "a sufficiently long password",
        },
    )

    assert response.status_code == 403
    assert "secure session expired" in response.get_data(as_text=True).lower()


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
