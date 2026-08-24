from __future__ import annotations

import pytest

import app as app_module
from mission_control import config, status, web_security


@pytest.fixture
def client(tmp_path, monkeypatch):
    database_path = tmp_path / "uninitialized-oap.db"
    monkeypatch.setattr(config, "OAP_DATABASE_PATH", str(database_path))
    monkeypatch.setattr(status, "_probe_ollama", lambda: False)

    app_module.app.config.update(TESTING=True, SESSION_COOKIE_SECURE=False)
    web_security.CHAT_BURST_LIMITER.reset()
    web_security.PUBLIC_WRITE_LIMITER.reset()
    app_module.signal_posts.clear()
    app_module.team_messages.clear()
    app_module.flag_counts.clear()
    app_module.profiles.clear()

    with app_module.app.test_client() as test_client:
        yield test_client

    app_module.signal_posts.clear()
    app_module.team_messages.clear()
    app_module.flag_counts.clear()
    app_module.profiles.clear()
    web_security.CHAT_BURST_LIMITER.reset()
    web_security.PUBLIC_WRITE_LIMITER.reset()


@pytest.fixture
def csrf(client):
    with client.session_transaction() as current_session:
        current_session[web_security.CSRF_SESSION_KEY] = (
            "test-csrf-token-value-1234567890"
        )
    return {"csrf_token": "test-csrf-token-value-1234567890"}
