from __future__ import annotations

import hashlib
import time

import app as app_module
import smi_gateway
from mission_control import founder_recovery, neon_auth, web_security

RECOVERY_CODE = "oap-founder-recovery-test-code-1234567890"


def _enable_recovery(monkeypatch, *, seconds: int = 3600) -> None:
    monkeypatch.setenv("OAP_SESSION_SECRET", "s" * 64)
    monkeypatch.setenv(
        founder_recovery.RECOVERY_TOKEN_HASH_ENV,
        hashlib.sha256(RECOVERY_CODE.encode("utf-8")).hexdigest(),
    )
    monkeypatch.setenv(
        founder_recovery.RECOVERY_EXPIRES_AT_ENV,
        str(int(time.time()) + seconds),
    )


def _csrf_for(client) -> str:
    with client.session_transaction() as current_session:
        value = current_session.get(web_security.CSRF_SESSION_KEY)
    assert isinstance(value, str) and len(value) >= 32
    return value


def test_recovery_is_hidden_when_not_server_configured(anonymous_client):
    response = anonymous_client.get("/auth/recover-founder")

    assert response.status_code == 404
    assert response.headers["Cache-Control"] == "no-store"


def test_gateway_only_recovery_boundary(anonymous_client, monkeypatch):
    _enable_recovery(monkeypatch)
    monkeypatch.setenv("OAP_SURFACE_ROLE", "public")
    monkeypatch.setenv("OAP_SMI_GATEWAY_SECRET", "g" * 64)

    direct = anonymous_client.get("/auth/recover-founder")
    through_gateway = anonymous_client.get(
        "/auth/recover-founder",
        headers={"X-OAP-SMI-Gateway": "g" * 64},
    )

    assert direct.status_code == 404
    assert through_gateway.status_code == 200
    assert "Founder recovery code" in through_gateway.get_data(as_text=True)


def test_invalid_recovery_code_fails_closed(anonymous_client, monkeypatch):
    _enable_recovery(monkeypatch)
    page = anonymous_client.get("/auth/recover-founder")
    assert page.status_code == 200

    response = anonymous_client.post(
        "/auth/recover-founder",
        data={
            "csrf_token": _csrf_for(anonymous_client),
            "recovery_code": "wrong-recovery-code-that-is-long-enough-123456",
            "next": "/mission/ollama",
        },
    )

    assert response.status_code == 403
    assert "not recognised" in response.get_data(as_text=True)
    with anonymous_client.session_transaction() as current_session:
        assert founder_recovery.RECOVERY_SESSION_KEY not in current_session


def test_recovery_opens_mission_control_without_neon_and_blocks_my_world(
    anonymous_client, monkeypatch
):
    _enable_recovery(monkeypatch)
    assert anonymous_client.get("/auth/recover-founder").status_code == 200
    token = _csrf_for(anonymous_client)

    response = anonymous_client.post(
        "/auth/recover-founder",
        data={
            "csrf_token": token,
            "recovery_code": RECOVERY_CODE,
            "next": "/mission/ollama",
        },
    )
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/mission/ollama")

    def unavailable(_cookie_header):
        raise neon_auth.AuthUnavailable("database_unavailable")

    monkeypatch.setattr(neon_auth, "get_session", unavailable)

    private_asset = anonymous_client.get("/mission/static/mission_control.css")
    assert private_asset.status_code == 200

    my_world = anonymous_client.get("/my-world")
    assert my_world.status_code == 302
    assert "/auth?next=" in my_world.headers["Location"]
    assert "auth_error=unavailable" in my_world.headers["Location"]


def test_recovery_session_is_bounded_to_fifteen_minutes(anonymous_client, monkeypatch):
    _enable_recovery(monkeypatch, seconds=3600)
    now = int(time.time())

    with app_module.app.test_request_context("/"):
        expires_at = founder_recovery.begin_session(now=now)
        assert expires_at == now + founder_recovery.SESSION_MAX_SECONDS
        assert founder_recovery.session_active(now=now + 899) is True
        assert founder_recovery.session_active(now=now + 900) is False


def test_recovery_rejects_external_redirects(anonymous_client, monkeypatch):
    _enable_recovery(monkeypatch)
    assert anonymous_client.get("/auth/recover-founder").status_code == 200

    response = anonymous_client.post(
        "/auth/recover-founder",
        data={
            "csrf_token": _csrf_for(anonymous_client),
            "recovery_code": RECOVERY_CODE,
            "next": "//evil.example/private",
        },
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/mission/ollama")


def test_smi_gateway_allows_recovery_but_keeps_signup_blocked():
    assert smi_gateway._allowed("/auth/recover-founder") is True
    assert smi_gateway._allowed("/auth/sign-up") is False
