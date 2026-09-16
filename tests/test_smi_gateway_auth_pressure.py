from __future__ import annotations

import smi_gateway


class _Headers(dict):
    def get_all(self, _name):
        return []


class _Response:
    def __init__(self, status: int, body: bytes = b"upstream"):
        self.status = status
        self.code = status
        self.headers = _Headers({"Content-Type": "text/plain"})
        self._body = body
        self.closed = False

    def read(self, _size=-1):
        if not self._body:
            return b""
        body, self._body = self._body, b""
        return body

    def close(self):
        self.closed = True


class _Opener:
    def __init__(self, *responses):
        self.responses = list(responses)
        self.calls = 0

    def open(self, _request, timeout=120):
        assert timeout == 120
        self.calls += 1
        return self.responses.pop(0)


def _configure(monkeypatch):
    monkeypatch.setenv("OAP_SMI_GATEWAY_SECRET", "g" * 64)
    monkeypatch.setenv("OAP_PUBLIC_ORIGIN", "https://public.example.test")
    monkeypatch.delenv("RENDER", raising=False)


def test_founder_auth_get_retries_one_transient_edge_429(monkeypatch):
    _configure(monkeypatch)
    opener = _Opener(_Response(429), _Response(200, b"Founder auth"))
    monkeypatch.setattr(smi_gateway, "_OPENER", opener)
    monkeypatch.setattr(smi_gateway.time, "sleep", lambda _seconds: None)

    response = smi_gateway.app.test_client().get("/auth?next=/mission/ollama")

    assert opener.calls == 2
    assert response.status_code == 200
    assert response.get_data() == b"Founder auth"


def test_founder_auth_get_normalizes_persistent_edge_429(monkeypatch):
    _configure(monkeypatch)
    opener = _Opener(_Response(429), _Response(429))
    monkeypatch.setattr(smi_gateway, "_OPENER", opener)
    monkeypatch.setattr(smi_gateway.time, "sleep", lambda _seconds: None)

    response = smi_gateway.app.test_client().get("/auth?next=/mission/ollama")

    assert opener.calls == 2
    assert response.status_code == 503
    assert response.headers["Retry-After"] == "5"
    assert response.headers["X-OAP-Auth-Upstream"] == "rate-limited"
    assert b"Too many requests" not in response.get_data()


def test_founder_password_post_is_never_replayed_on_429(monkeypatch):
    _configure(monkeypatch)
    opener = _Opener(_Response(429))
    monkeypatch.setattr(smi_gateway, "_OPENER", opener)

    response = smi_gateway.app.test_client().post(
        "/auth/sign-in",
        data={"password": "private-value", "next": "/mission/ollama"},
    )

    assert opener.calls == 1
    assert response.status_code == 503
    assert response.headers["Retry-After"] == "5"
    assert b"private-value" not in response.get_data()


def test_non_auth_429_keeps_existing_rate_limit_semantics(monkeypatch):
    _configure(monkeypatch)
    opener = _Opener(_Response(429, b"bounded private route"))
    monkeypatch.setattr(smi_gateway, "_OPENER", opener)

    response = smi_gateway.app.test_client().get("/mission/status")

    assert opener.calls == 1
    assert response.status_code == 429
    assert response.get_data() == b"bounded private route"
