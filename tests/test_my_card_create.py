from __future__ import annotations

from pathlib import Path

from mission_control import neon_auth, web_security


def test_public_my_card_page_is_free_and_not_enter_my_world(anonymous_client):
    response = anonymous_client.get("/my-card/create")
    page = response.get_data(as_text=True)

    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    assert "Create My Card — Free" in page
    assert "OAP World and public Link Up are open without an account, email or sign-in." in page
    assert "No email or sign-in is needed." in page
    assert "Continue without My Card" in page
    assert 'href="/linkup"' in page
    assert "Email — optional" in page
    assert "Password — optional" in page
    assert "Leave blank for a basic My Card." in page
    assert "If you leave password blank, leave email blank too." in page
    assert 'name="email" type="email" autocomplete="email" maxlength="320"' in page
    assert 'aria-describedby="card-email-note"' in page
    assert 'aria-describedby="card-email-note" required' not in page
    assert "Enter My World" not in page
    assert 'action="/my-card/create"' in page
    assert 'name="csrf_token"' in page


def test_public_my_card_creation_sets_first_party_session_and_opens_my_card(
    anonymous_client, monkeypatch
):
    token = "my-card-create-csrf-token-value-123456789"
    with anonymous_client.session_transaction() as current_session:
        current_session[web_security.CSRF_SESSION_KEY] = token
    observed = {}

    def fake_sign_up(name, email, password):
        observed["values"] = (name, email, password)
        return neon_auth.AuthResult(
            status_code=200,
            payload={"user": {"id": "22222222-2222-4222-8222-222222222222"}},
            set_cookie_headers=(
                "better-auth.session_token=new-member; Secure; HttpOnly",
            ),
        )

    monkeypatch.setattr(neon_auth, "sign_up", fake_sign_up)
    response = anonymous_client.post(
        "/my-card/create",
        data={
            "csrf_token": token,
            "name": "New Member",
            "email": "NEW@EXAMPLE.TEST",
            "password": "a-private-password",
            "password_confirmation": "a-private-password",
            "accept_private_actions": "yes",
        },
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/my-card")
    assert observed["values"] == (
        "New Member",
        "new@example.test",
        "a-private-password",
    )
    auth_cookie = next(
        value
        for value in response.headers.getlist("Set-Cookie")
        if value.startswith("better-auth.session_token=")
    )
    assert "Path=/; Secure; HttpOnly; SameSite=Lax" in auth_cookie


def test_public_my_card_creation_rejects_missing_consent_without_auth_call(
    anonymous_client, monkeypatch
):
    token = "my-card-consent-csrf-token-value-123456789"
    with anonymous_client.session_transaction() as current_session:
        current_session[web_security.CSRF_SESSION_KEY] = token

    monkeypatch.setattr(
        neon_auth,
        "sign_up",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("auth must not be called")
        ),
    )
    response = anonymous_client.post(
        "/my-card/create",
        data={
            "csrf_token": token,
            "name": "New Member",
            "email": "new@example.test",
            "password": "a-private-password",
            "password_confirmation": "a-private-password",
        },
    )

    assert response.status_code == 400
    assert "Confirm the My Card privacy and private-action boundary." in response.get_data(as_text=True)


def test_public_my_card_creation_allows_blank_email(
    anonymous_client, monkeypatch
):
    token = "my-card-optional-email-csrf-token-value-123456789"
    with anonymous_client.session_transaction() as current_session:
        current_session[web_security.CSRF_SESSION_KEY] = token
    observed = {}

    def fake_sign_up(name, email, password):
        observed["values"] = (name, email, password)
        return neon_auth.AuthResult(
            status_code=200,
            payload={"user": {"id": "33333333-3333-4333-8333-333333333333"}},
            set_cookie_headers=(
                "better-auth.session_token=email-optional; Secure; HttpOnly",
            ),
        )

    monkeypatch.setattr(neon_auth, "sign_up", fake_sign_up)
    response = anonymous_client.post(
        "/my-card/create",
        data={
            "csrf_token": token,
            "name": "No Email Member",
            "email": "",
            "password": "a-private-password",
            "password_confirmation": "a-private-password",
            "accept_private_actions": "yes",
        },
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/my-card")
    assert observed["values"] == (
        "No Email Member",
        "",
        "a-private-password",
    )



def test_public_my_card_creation_allows_blank_password_without_auth_call(
    anonymous_client, monkeypatch
):
    token = "my-card-password-optional-csrf-token-value-123456789"
    with anonymous_client.session_transaction() as current_session:
        current_session[web_security.CSRF_SESSION_KEY] = token

    monkeypatch.setattr(
        neon_auth,
        "sign_up",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("managed auth must not be called for a basic card")
        ),
    )
    response = anonymous_client.post(
        "/my-card/create",
        data={
            "csrf_token": token,
            "name": "Basic Card Member",
            "email": "",
            "password": "",
            "password_confirmation": "",
            "accept_private_actions": "yes",
        },
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/my-card")

    page = anonymous_client.get("/linkup").get_data(as_text=True)
    assert "Basic Card Member" in page
    assert "Basic My Card active. No password required." in page
    assert "Private Link Up stays locked until secure sign-in is added." in page


def test_passwordless_basic_card_does_not_accept_email_without_secure_sign_in(
    anonymous_client, monkeypatch
):
    token = "my-card-passwordless-email-csrf-token-value-123456789"
    with anonymous_client.session_transaction() as current_session:
        current_session[web_security.CSRF_SESSION_KEY] = token

    monkeypatch.setattr(
        neon_auth,
        "sign_up",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("managed auth must not be called")
        ),
    )
    response = anonymous_client.post(
        "/my-card/create",
        data={
            "csrf_token": token,
            "name": "Basic Card Member",
            "email": "private@example.test",
            "password": "",
            "password_confirmation": "",
            "accept_private_actions": "yes",
        },
    )

    assert response.status_code == 400
    assert "either set a password or leave email blank" in response.get_data(as_text=True)



def test_basic_my_card_hub_shows_profile_contacts_settings_and_emojis(anonymous_client, monkeypatch):
    token = "my-card-hub-csrf-token-value-123456789"
    with anonymous_client.session_transaction() as current_session:
        current_session[web_security.CSRF_SESSION_KEY] = token

    monkeypatch.setattr(
        neon_auth,
        "sign_up",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("managed auth must not be called")
        ),
    )
    response = anonymous_client.post(
        "/my-card/create",
        data={
            "csrf_token": token,
            "name": "Hub Member",
            "email": "",
            "password": "",
            "password_confirmation": "",
            "accept_private_actions": "yes",
        },
    )
    assert response.headers["Location"].endswith("/my-card")

    page = anonymous_client.get("/my-card").get_data(as_text=True)
    assert "Hub Member" in page
    assert "Contacts" in page
    assert "Settings · Theme · My Emojis" in page
    assert "DP avatar" in page
    assert "DP photo upload is not enabled yet." in page
    assert "Discover People" in page
    assert "Link Up" in page


def test_my_card_preferences_save_theme_avatar_and_my_emojis(anonymous_client):
    token = "my-card-prefs-csrf-token-value-123456789"
    with anonymous_client.session_transaction() as current_session:
        current_session[web_security.CSRF_SESSION_KEY] = token
        current_session["oap_public_my_card"] = {
            "identity_id": "44444444-4444-4444-8444-444444444444",
            "card_id": "OAP-44444444",
            "display_name": "Prefs Member",
            "credentialed": False,
        }

    response = anonymous_client.post(
        "/my-card/preferences",
        data={
            "csrf_token": token,
            "theme": "midnight",
            "avatar": "🐆",
            "emoji": ["👑", "🐆", "✨"],
        },
    )
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/my-card")

    page = anonymous_client.get("/my-card").get_data(as_text=True)
    assert 'data-my-card-theme="midnight"' in page
    assert "🐆" in page
    assert 'value="✨" checked' in page
