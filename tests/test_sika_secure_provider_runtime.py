import hashlib
import hmac
import json

import pytest

from mission_control import sika_secure_provider_runtime as runtime

PAYMENT_ENV = {
    "OAP_PAYMENT_PROVIDER_ID": "private-provider",
    "OAP_PAYMENT_PROVIDER_BASE_URL": "https://payments.example.test",
    "OAP_PAYMENT_PROVIDER_ALLOWED_HOST": "payments.example.test",
    "OAP_PAYMENT_PROVIDER_TOKEN": "super-secret-token",
    "OAP_PAYMENT_PROVIDER_WEBHOOK_SECRET": "webhook-secret",
    "OAP_PAYMENT_PROVIDER_EXECUTION_ENABLED": "true",
}


def _set_payment_env(monkeypatch):
    for key, value in PAYMENT_ENV.items():
        monkeypatch.setenv(key, value)


def test_configuration_status_never_exposes_secret_values(monkeypatch):
    _set_payment_env(monkeypatch)
    status = runtime.configuration_status("payment")

    assert status["configuration_complete"] is True
    assert status["execution_enabled"] is True
    assert status["token_present"] is True
    assert status["webhook_secret_present"] is True
    assert status["secret_values_exposed"] is False
    encoded = json.dumps(status)
    assert "super-secret-token" not in encoded
    assert "webhook-secret" not in encoded


def test_execution_fails_closed_without_explicit_enable(monkeypatch):
    _set_payment_env(monkeypatch)
    monkeypatch.setenv("OAP_PAYMENT_PROVIDER_EXECUTION_ENABLED", "false")

    with pytest.raises(runtime.SecureProviderError, match="execution_disabled"):
        runtime.submit(
            kind="payment",
            payload={"amount": "10.00"},
            idempotency_key="payment:12345678",
        )


def test_execution_rejects_non_https_and_host_mismatch(monkeypatch):
    _set_payment_env(monkeypatch)
    monkeypatch.setenv(
        "OAP_PAYMENT_PROVIDER_BASE_URL",
        "http://payments.example.test",
    )
    with pytest.raises(runtime.SecureProviderError, match="https_required"):
        runtime.configuration_status("payment")

    monkeypatch.setenv(
        "OAP_PAYMENT_PROVIDER_BASE_URL",
        "https://other.example.test",
    )
    with pytest.raises(runtime.SecureProviderError, match="host_not_allowed"):
        runtime.configuration_status("payment")


def test_submit_uses_idempotency_and_returns_sanitized_receipt(monkeypatch):
    _set_payment_env(monkeypatch)
    captured = {}

    class Response:
        status = 201

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self, limit):
            return json.dumps({
                "provider_reference": "pay_123",
                "status": "accepted",
            }).encode()

    class Opener:
        def open(self, req, timeout):
            captured["url"] = req.full_url
            captured["authorization"] = req.headers.get("Authorization")
            captured["idempotency"] = req.headers.get("Idempotency-key")
            captured["timeout"] = timeout
            return Response()

    monkeypatch.setattr(runtime.request, "build_opener", lambda *args: Opener())

    receipt = runtime.submit(
        kind="payment",
        payload={"amount": "10.00", "currency": "GBP"},
        idempotency_key="payment:12345678",
    )

    assert captured["url"] == "https://payments.example.test/v1/submit"
    assert captured["authorization"] == "Bearer super-secret-token"
    assert captured["idempotency"] == "payment:12345678"
    assert receipt["provider_reference"] == "pay_123"
    assert receipt["provider_execution_performed"] is True
    assert receipt["secret_values_exposed"] is False
    assert "super-secret-token" not in json.dumps(receipt)


def test_submit_requires_provider_reference(monkeypatch):
    _set_payment_env(monkeypatch)

    class Response:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self, limit):
            return b'{"status":"accepted"}'

    class Opener:
        def open(self, req, timeout):
            return Response()

    monkeypatch.setattr(runtime.request, "build_opener", lambda *args: Opener())

    with pytest.raises(runtime.SecureProviderError, match="provider_reference_missing"):
        runtime.submit(
            kind="payment",
            payload={"amount": "10.00"},
            idempotency_key="payment:12345678",
        )


def test_webhook_signature_is_constant_time_verified(monkeypatch):
    _set_payment_env(monkeypatch)
    body = b'{"provider_reference":"pay_123","status":"settled"}'
    timestamp = 1_790_000_000
    signature = hmac.new(
        b"webhook-secret",
        f"{timestamp}.".encode() + body,
        hashlib.sha256,
    ).hexdigest()

    verified = runtime.verify_webhook(
        kind="payment",
        body=body,
        timestamp=timestamp,
        signature=f"sha256={signature}",
        now=timestamp,
    )
    assert verified["signature_verified"] is True
    assert verified["secret_values_exposed"] is False

    rejected = runtime.verify_webhook(
        kind="payment",
        body=body,
        timestamp=timestamp,
        signature="sha256=" + ("0" * 64),
        now=timestamp,
    )
    assert rejected["signature_verified"] is False


def test_webhook_replay_window_is_enforced(monkeypatch):
    _set_payment_env(monkeypatch)

    with pytest.raises(
        runtime.SecureProviderError,
        match="timestamp_outside_tolerance",
    ):
        runtime.verify_webhook(
            kind="payment",
            body=b"{}",
            timestamp=100,
            signature="0" * 64,
            now=1000,
            tolerance_seconds=300,
        )


def test_pod_and_payment_are_separate_secret_scopes(monkeypatch):
    _set_payment_env(monkeypatch)
    monkeypatch.setenv("OAP_POD_PROVIDER_ID", "private-pod")
    monkeypatch.setenv("OAP_POD_PROVIDER_BASE_URL", "https://pod.example.test")
    monkeypatch.setenv("OAP_POD_PROVIDER_ALLOWED_HOST", "pod.example.test")
    monkeypatch.setenv("OAP_POD_PROVIDER_TOKEN", "pod-secret")
    monkeypatch.setenv("OAP_POD_PROVIDER_WEBHOOK_SECRET", "pod-hook")
    monkeypatch.setenv("OAP_POD_PROVIDER_EXECUTION_ENABLED", "true")

    status = runtime.status()
    assert status["payment_configuration"]["configuration_complete"] is True
    assert status["pod_configuration"]["configuration_complete"] is True
    encoded = json.dumps(status)
    for secret in ("super-secret-token", "webhook-secret", "pod-secret", "pod-hook"):
        assert secret not in encoded
    assert status["zero_bypass_policy"] is True
