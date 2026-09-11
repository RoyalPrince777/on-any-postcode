import pytest
from flask import Flask

from mission_control import smi_chat_runtime_core, web_security


def test_private_smi_chat_burst_cap_allows_active_conversation():
    limiter = web_security.CHAT_BURST_LIMITER
    assert limiter.limit == 30
    assert limiter.window_seconds == 60
    assert limiter.duplicate_seconds == 1.0
    assert limiter.fingerprint_request_body is True


def test_only_exact_duplicate_retry_is_coalesced(monkeypatch):
    app = Flask(__name__)
    times = iter((100.0, 100.5, 101.5, 102.5, 103.5))
    monkeypatch.setattr(web_security.time, "monotonic", lambda: next(times))
    limiter = web_security.SlidingWindowLimiter(
        limit=3,
        window_seconds=60,
        duplicate_seconds=1.0,
        fingerprint_request_body=True,
    )

    with app.test_request_context("/chat", method="POST", json={"message": "same"}):
        assert limiter.allow("founder") is True
    with app.test_request_context("/chat", method="POST", json={"message": "same"}):
        assert limiter.allow("founder") is True  # exact retry; no extra slot
    with app.test_request_context("/chat", method="POST", json={"message": "different-1"}):
        assert limiter.allow("founder") is True
    with app.test_request_context("/chat", method="POST", json={"message": "different-2"}):
        assert limiter.allow("founder") is True
    with app.test_request_context("/chat", method="POST", json={"message": "different-3"}):
        assert limiter.allow("founder") is False


def test_private_smi_hard_cap_rejects_request_31(monkeypatch):
    app = Flask(__name__)
    times = iter(200.0 + (index * 0.01) for index in range(31))
    monkeypatch.setattr(web_security.time, "monotonic", lambda: next(times))
    limiter = web_security.SlidingWindowLimiter(
        limit=30,
        window_seconds=60,
        duplicate_seconds=1.0,
        fingerprint_request_body=True,
    )

    for index in range(30):
        with app.test_request_context(
            "/chat", method="POST", json={"message": f"distinct-{index}"}
        ):
            assert limiter.allow("founder") is True

    with app.test_request_context(
        "/chat", method="POST", json={"message": "distinct-30"}
    ):
        assert limiter.allow("founder") is False


def test_public_and_founder_auth_limiters_are_unchanged():
    public = web_security.PUBLIC_WRITE_LIMITER
    assert public.limit == 30
    assert public.window_seconds == 60
    assert public.duplicate_seconds == 0.35
    assert public.fingerprint_request_body is False

    founder_auth = web_security.AUTH_BURST_LIMITER
    assert founder_auth.limit == 10
    assert founder_auth.window_seconds == 15 * 60
    assert founder_auth.duplicate_seconds == 2.0
    assert founder_auth.fingerprint_request_body is False


class _CountResult:
    def __init__(self, count: int):
        self.count = count

    def fetchone(self):
        return (self.count,)


class _CountConnection:
    def __init__(self, count: int):
        self.count = count

    def execute(self, _query, _params):
        return _CountResult(self.count)


def test_neon_backed_chat_limiter_remains_separately_configurable(monkeypatch):
    connection = _CountConnection(12)

    monkeypatch.setenv("OAP_CHAT_RATE_LIMIT", "12")
    with pytest.raises(ValueError, match="chat_rate_limit"):
        smi_chat_runtime_core._chat_rate_limit(connection, "founder")

    monkeypatch.setenv("OAP_CHAT_RATE_LIMIT", "13")
    smi_chat_runtime_core._chat_rate_limit(connection, "founder")
