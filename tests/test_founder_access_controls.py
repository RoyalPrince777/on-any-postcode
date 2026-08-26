from __future__ import annotations

from mission_control import neon_auth


NON_FOUNDER_ID = "22222222-2222-4222-8222-222222222222"


def test_private_signup_rejects_non_founder_before_auth_provider(monkeypatch):
    monkeypatch.setenv("OAP_HUMAN_AUTHORITY_EMAIL", "founder@example.test")

    def forbidden_request(*args, **kwargs):
        del args, kwargs
        raise AssertionError("non-Founder signup must not contact Neon Auth")

    monkeypatch.setattr(neon_auth, "_request", forbidden_request)

    result = neon_auth.sign_up("Other", "other@example.test", "private password")

    assert result.status_code == 403
    assert result.set_cookie_headers == ()


def test_founder_signup_never_auto_establishes_private_session(monkeypatch):
    monkeypatch.setenv("OAP_HUMAN_AUTHORITY_EMAIL", "founder@example.test")
    observed = {}

    def fake_request(path, *, method, payload=None, cookie_header=None):
        observed.update(
            path=path,
            method=method,
            payload=payload,
            cookie_header=cookie_header,
        )
        return neon_auth.AuthResult(
            status_code=200,
            payload={"user": {"id": NON_FOUNDER_ID}},
            set_cookie_headers=("better-auth.session_token=upstream-session",),
        )

    monkeypatch.setattr(neon_auth, "_request", fake_request)

    result = neon_auth.sign_up("Founder", "FOUNDER@example.test", "private password")

    assert observed["path"] == "/sign-up/email"
    assert observed["payload"]["email"] == "FOUNDER@example.test"
    assert result.status_code == 200
    assert result.set_cookie_headers == ()


def test_authenticated_non_founder_cannot_enter_mission_control(
    anonymous_client, monkeypatch
):
    def non_founder_session(cookie_header):
        assert "better-auth.session_token=other-session" in cookie_header
        return neon_auth.AuthResult(
            status_code=200,
            payload={
                "session": {"id": "other-session"},
                "user": {
                    "id": NON_FOUNDER_ID,
                    "name": "Other Member",
                    "email": "other@example.test",
                    "emailVerified": True,
                },
            },
        )

    monkeypatch.setattr(neon_auth, "get_session", non_founder_session)
    anonymous_client.set_cookie("better-auth.session_token", "other-session")
    with anonymous_client.session_transaction() as current_session:
        current_session[neon_auth.AUTH_COOKIE_NAMES_SESSION_KEY] = [
            "better-auth.session_token"
        ]

    response = anonymous_client.get("/mission")

    assert response.status_code == 403
    assert response.get_json()["error"]["code"] == "human_authority_required"
    assert response.headers["Cache-Control"] == "no-store"


def test_founder_selector_accepts_verified_test_identity(client):
    assert client.get("/mission").status_code == 200
