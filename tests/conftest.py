from __future__ import annotations

import pytest

import app as app_module
from mission_control import config, neon_auth, status, web_security

TEST_AUTH_ID = "11111111-1111-4111-8111-111111111111"
TEST_AUTH_COOKIE = "better-auth.session_token"


def _fake_auth_session(cookie_header):
    if f"{TEST_AUTH_COOKIE}=verified-test-session" not in cookie_header:
        return neon_auth.AuthResult(status_code=200, payload=None)
    return neon_auth.AuthResult(
        status_code=200,
        payload={
            "session": {"id": "test-session"},
            "user": {
                "id": TEST_AUTH_ID,
                "name": "OAP Member",
                "email": "member@example.test",
                "emailVerified": True,
            },
        },
    )


def _configure_test_app(tmp_path, monkeypatch):
    database_path = tmp_path / "uninitialized-oap.db"
    monkeypatch.setattr(config, "OAP_DATABASE_PATH", str(database_path))
    monkeypatch.setattr(status, "_probe_ollama", lambda: False)
    monkeypatch.setattr(neon_auth, "get_session", _fake_auth_session)
    monkeypatch.setenv(
        "NEON_AUTH_BASE_URL", "https://example.neonauth.test/neondb/auth"
    )
    monkeypatch.setenv("OAP_HUMAN_AUTHORITY_EMAIL", "member@example.test")
    monkeypatch.setenv("OAP_AUTH_REQUIRED", "true")

    app_module.app.config.update(TESTING=True, SESSION_COOKIE_SECURE=False)
    web_security.CHAT_BURST_LIMITER.reset()
    web_security.PUBLIC_WRITE_LIMITER.reset()
    web_security.AUTH_BURST_LIMITER.reset()
    app_module.signal_posts.clear()
    app_module.team_messages.clear()
    app_module.flag_counts.clear()
    app_module.profiles.clear()


def _cleanup_test_app():
    app_module.signal_posts.clear()
    app_module.team_messages.clear()
    app_module.flag_counts.clear()
    app_module.profiles.clear()
    web_security.CHAT_BURST_LIMITER.reset()
    web_security.PUBLIC_WRITE_LIMITER.reset()
    web_security.AUTH_BURST_LIMITER.reset()


@pytest.fixture
def client(tmp_path, monkeypatch):
    _configure_test_app(tmp_path, monkeypatch)

    with app_module.app.test_client() as test_client:
        test_client.set_cookie(TEST_AUTH_COOKIE, "verified-test-session")
        with test_client.session_transaction() as current_session:
            current_session[neon_auth.AUTH_COOKIE_NAMES_SESSION_KEY] = [
                TEST_AUTH_COOKIE
            ]
        yield test_client

    _cleanup_test_app()


@pytest.fixture
def anonymous_client(tmp_path, monkeypatch):
    _configure_test_app(tmp_path, monkeypatch)

    with app_module.app.test_client() as test_client:
        yield test_client

    _cleanup_test_app()


@pytest.fixture
def csrf(client):
    with client.session_transaction() as current_session:
        current_session[web_security.CSRF_SESSION_KEY] = (
            "test-csrf-token-value-1234567890"
        )
    return {"csrf_token": "test-csrf-token-value-1234567890"}
