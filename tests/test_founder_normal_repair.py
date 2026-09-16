from __future__ import annotations

import hashlib

from mission_control import founder_local_auth, founder_recovery_views, web_security


def _configure(monkeypatch, *, token: str = "normal-founder-repair-proof-value-1234567890"):
    monkeypatch.setattr(founder_recovery_views.time, "time", lambda: 1000)
    monkeypatch.setenv(
        "OAP_FOUNDER_NORMAL_REPAIR_TOKEN_SHA256",
        hashlib.sha256(token.encode("utf-8")).hexdigest(),
    )
    monkeypatch.setenv("OAP_FOUNDER_NORMAL_REPAIR_EXPIRES_AT", "2000")
    return token


def test_normal_repair_is_hidden_without_server_proof(anonymous_client, monkeypatch):
    monkeypatch.delenv("OAP_FOUNDER_NORMAL_REPAIR_TOKEN_SHA256", raising=False)
    monkeypatch.delenv("OAP_FOUNDER_NORMAL_REPAIR_EXPIRES_AT", raising=False)

    response = anonymous_client.get("/auth/repair-founder-password")

    assert response.status_code == 404


def test_normal_repair_rejects_wrong_proof(anonymous_client, monkeypatch):
    _configure(monkeypatch)

    response = anonymous_client.get(
        "/auth/repair-founder-password?proof=wrong-proof-value-that-is-long-enough"
    )

    assert response.status_code == 404


def test_normal_repair_proof_is_stripped_before_password_form(
    anonymous_client, monkeypatch
):
    token = _configure(monkeypatch)

    response = anonymous_client.get(
        "/auth/repair-founder-password",
        query_string={"proof": token, "next": "/mission/ollama"},
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith(
        "/auth/repair-founder-password?next=/mission/ollama"
    )
    assert "proof=" not in response.headers["Location"]

    page = anonymous_client.get(response.headers["Location"])
    assert page.status_code == 200
    html = page.get_data(as_text=True)
    assert "Restore normal Founder login" in html
    assert 'name="action" value="repair-normal-password"' in html
    assert token not in html


def test_normal_repair_is_independent_of_lost_recovery_code(
    anonymous_client, monkeypatch
):
    token = _configure(monkeypatch)
    monkeypatch.setattr(
        founder_recovery_views.founder_recovery,
        "configured",
        lambda: False,
    )

    response = anonymous_client.get(
        "/auth/repair-founder-password",
        query_string={"proof": token, "next": "/mission/ollama"},
    )

    assert response.status_code == 302
    page = anonymous_client.get(response.headers["Location"])
    assert page.status_code == 200


def test_normal_repair_rebinds_same_founder_then_returns_to_normal_login(
    anonymous_client, monkeypatch
):
    token = _configure(monkeypatch)
    monkeypatch.setattr(
        founder_local_auth,
        "bind_existing_password",
        lambda password: (
            "rebound" if password == "existing-private-password" else "unexpected"
        ),
    )

    proof_response = anonymous_client.get(
        "/auth/repair-founder-password",
        query_string={"proof": token, "next": "/mission/ollama"},
    )
    assert proof_response.status_code == 302
    page = anonymous_client.get(proof_response.headers["Location"])
    assert page.status_code == 200

    with anonymous_client.session_transaction() as current_session:
        csrf = current_session[web_security.CSRF_SESSION_KEY]

    response = anonymous_client.post(
        "/auth/repair-founder-password",
        data={
            "action": "repair-normal-password",
            "csrf_token": csrf,
            "password": "existing-private-password",
            "password_confirmation": "existing-private-password",
            "next": "/mission/ollama",
        },
    )

    assert response.status_code == 302
    assert "/enter-my-world?next=/mission/ollama" in response.headers["Location"]
    assert "render_bound=1" in response.headers["Location"]
    assert response.headers["X-OAP-Founder-Lane"] == "render-local-normal"
    assert response.headers["X-OAP-Founder-Password-State"] == "rebound"

    expired_session = anonymous_client.get(
        "/auth/repair-founder-password?next=/mission/ollama"
    )
    assert expired_session.status_code == 404


def test_normal_repair_session_expires_fail_closed(anonymous_client, monkeypatch):
    token = _configure(monkeypatch)

    response = anonymous_client.get(
        "/auth/repair-founder-password",
        query_string={"proof": token, "next": "/mission/ollama"},
    )
    assert response.status_code == 302

    monkeypatch.setattr(founder_recovery_views.time, "time", lambda: 2001)
    expired = anonymous_client.get(response.headers["Location"])
    assert expired.status_code == 404
