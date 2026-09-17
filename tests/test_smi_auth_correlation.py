import importlib
import logging


def test_auth_trace_is_privacy_safe(caplog):
    gateway = importlib.import_module("smi_gateway")
    trace = getattr(gateway, "_auth_trace", None)
    assert callable(trace), "A7 correlation instrumentation is not implemented"

    with (
        gateway.app.test_request_context(
            "/auth/sign-in",
            method="POST",
            data={"email": "founder@example.invalid", "password": "DO-NOT-LOG"},
            headers={
                "Cookie": "oap_founder_session=DO-NOT-LOG-COOKIE",
                "X-Forwarded-For": "203.0.113.42",
            },
        ),
        caplog.at_level(logging.INFO),
    ):
        trace("a7-test-request", "/auth/sign-in", 429, "normalized_rate_limit")

    text = caplog.text
    assert "a7-test-request" in text
    assert "normalized_rate_limit" in text
    assert "DO-NOT-LOG" not in text
    assert "DO-NOT-LOG-COOKIE" not in text
    assert "founder@example.invalid" not in text
    assert "203.0.113.42" not in text


def test_request_headers_forward_correlation_without_changing_client_identity(monkeypatch):
    gateway = importlib.import_module("smi_gateway")
    monkeypatch.setenv("OAP_SMI_GATEWAY_SECRET", "s" * 64)
    monkeypatch.setenv("RENDER", "true")

    with gateway.app.test_request_context(
        "/auth",
        headers={"X-Forwarded-For": "203.0.113.42, 10.0.0.2"},
        environ_base={"REMOTE_ADDR": "10.0.0.5"},
    ):
        try:
            headers = gateway._request_headers("a7-test-request")
        except TypeError as exc:
            raise AssertionError("A7 correlation header forwarding is not implemented") from exc

    assert headers["X-OAP-SMI-Gateway"] == "s" * 64
    assert headers["X-OAP-Client-IP"] == "203.0.113.42"
    assert headers["X-OAP-Request-ID"] == "a7-test-request"


def test_normalized_429_carries_correlation_evidence():
    gateway = importlib.import_module("smi_gateway")
    with gateway.app.test_request_context("/auth"):
        try:
            response = gateway._normalized_auth_rate_limit(
                "/auth", 429, correlation_id="a7-test-request"
            )
        except TypeError as exc:
            raise AssertionError("A7 normalized 429 correlation is not implemented") from exc

    assert response is not None
    assert response.status_code == 503
    assert response.headers["X-OAP-Request-ID"] == "a7-test-request"
    assert response.headers["X-OAP-Auth-Upstream"] == "rate-limited"
