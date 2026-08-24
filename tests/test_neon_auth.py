from __future__ import annotations

import json

from mission_control import neon_auth


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
