from __future__ import annotations

import smi_gateway


def test_gateway_founder_sign_in_503_uses_render_recovery():
    with smi_gateway.app.test_request_context("/auth/sign-in", method="POST"):
        response = smi_gateway._auth_unavailable_fallback(
            "/auth/sign-in",
            503,
            {},
        )

    assert response is not None
    assert response.status_code == 302
    assert response.headers["Location"] == (
        "/auth/recover-founder?next=/mission/ollama"
    )


def test_gateway_private_session_auth_outage_uses_render_recovery():
    headers = {
        "Location": (
            "https://on-any-postcode.onrender.com/auth"
            "?next=/mission/ollama&auth_error=unavailable"
        )
    }
    with smi_gateway.app.test_request_context("/mission/ollama", method="GET"):
        response = smi_gateway._auth_unavailable_fallback(
            "/mission/ollama",
            302,
            headers,
        )

    assert response is not None
    assert response.status_code == 302
    assert response.headers["Location"] == (
        "/auth/recover-founder?next=/mission/ollama"
    )


def test_gateway_normal_anonymous_auth_redirect_stays_on_password_lane():
    headers = {"Location": "/auth?next=/mission/ollama"}
    with smi_gateway.app.test_request_context("/mission/ollama", method="GET"):
        response = smi_gateway._auth_unavailable_fallback(
            "/mission/ollama",
            302,
            headers,
        )

    assert response is None


def test_gateway_non_auth_503_does_not_open_recovery():
    with smi_gateway.app.test_request_context("/mission/status", method="GET"):
        response = smi_gateway._auth_unavailable_fallback(
            "/mission/status",
            503,
            {},
        )

    assert response is None
