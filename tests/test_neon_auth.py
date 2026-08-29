from __future__ import annotations

import json

import pytest

from mission_control import neon_auth

NON_FOUNDER_ID = "22222222-2222-4222-8222-222222222222"


def test_auth_configuration_requires_branch_auth_https_url(monkeypatch):
    monkeypatch.setenv(
        "NEON_AUTH_BASE_URL", "https://example.neonauth.test/neondb/auth"
    )
    assert neon_auth.status() == {"configured": True, "valid": True}

    monkeypatch.setenv("NEON_AUTH_BASE_URL", "http://example.test/auth")
    assert neon_auth.status() == {"configured": True, "valid": False}


def test_scoped_cookie_removes_upstream_domain_and_enforces_first_party_flags():
    result = neon_auth.scoped_set_cookie(
        "better-auth.session_token=opaque; Domain=auth.example; "
        "Path=/provider; SameSite=None; Max-Age=3600"
    )

    assert result == (
        "better-auth.session_token=opaque; Path=/; Secure; HttpOnly; "
        "SameSite=Lax; Max-Age=3600"
    )


def test_cookie_header_forwards_only_recorded_auth_cookie_names():
    header = neon_auth.cookie_header(
        ["better-auth.session_token", "session", "missing"],
        {
            "better-auth.session_token": "opaque",
            "session": "signed-flask-cookie",
            "unrelated": "private-value",
        },
    )

    assert header == "better-auth.session_token=opaque"


def test_server_auth_request_omits_browser_origin_and_bounds_payload(
    monkeypatch,
):
    monkeypatch.setenv(
        "NEON_AUTH_BASE_URL", "https://example.neonauth.test/neondb/auth"
    )
    observed = {}

    class Headers:
        @staticmethod
        def get_all(_name):
            return []

    class Response:
        status = 200
        headers = Headers()

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            del exc_type, exc, traceback

        @staticmethod
        def read(_limit):
            return b'{"ok":true}'

    def fake_urlopen(request, timeout):
        observed["request"] = request
        observed["timeout"] = timeout
        return Response()

    monkeypatch.setattr(neon_auth.urlrequest, "urlopen", fake_urlopen)
    result = neon_auth.sign_in("member@example.test", "secret pass")
    request = observed["request"]

    assert result.payload == {"ok": True}
    assert request.get_header("Origin") is None
    assert request.get_header("Referer") is None
    assert json.loads(request.data) == {
        "email": "member@example.test",
        "password": "secret pass",
        "rememberMe": True,
    }
    assert observed["timeout"] == neon_auth.AUTH_TIMEOUT_SECONDS


def test_founder_signup_uses_only_the_server_side_selector(monkeypatch):
    monkeypatch.setenv("OAP_HUMAN_AUTHORITY_EMAIL", " Founder@Example.Test ")
    observed = {}

    def fake_request(path, *, method, payload=None, cookie_header=None):
        observed.update(
            path=path,
            method=method,
            payload=payload,
            cookie_header=cookie_header,
        )
        return neon_auth.AuthResult(status_code=200, payload={"user": {}})

    monkeypatch.setattr(neon_auth, "_request", fake_request)
    result = neon_auth.sign_up_founder("private passphrase", "OAP Founder")

    assert result.status_code == 200
    assert observed == {
        "path": "/sign-up/email",
        "method": "POST",
        "payload": {
            "name": "OAP Founder",
            "email": "founder@example.test",
            "password": "private passphrase",
        },
        "cookie_header": None,
    }


def test_founder_signup_fails_closed_without_server_selector(monkeypatch):
    monkeypatch.delenv("OAP_HUMAN_AUTHORITY_EMAIL", raising=False)

    with pytest.raises(neon_auth.AuthUnavailable):
        neon_auth.sign_up_founder("private passphrase", "OAP Founder")


def test_provider_error_code_never_returns_message_or_user_data():
    result = neon_auth.AuthResult(
        status_code=400,
        payload={
            "code": "PASSWORD_TOO_SHORT",
            "message": "private provider detail",
            "email": "member@example.test",
        },
    )

    assert neon_auth.safe_error_code(result) == "PASSWORD_TOO_SHORT"
    assert neon_auth.safe_error_code(
        neon_auth.AuthResult(
            status_code=400,
            payload={"code": "unsafe code with spaces", "message": "secret"},
        )
    ) == "unknown"


def test_private_selector_is_normalised_server_side(monkeypatch):
    monkeypatch.setenv("OAP_HUMAN_AUTHORITY_EMAIL", " Founder@Example.Test ")

    assert neon_auth.configured_founder_email() == "founder@example.test"


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
