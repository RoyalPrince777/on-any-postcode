from __future__ import annotations

import json

import pytest

from mission_control import printful_pod_adapter


@pytest.fixture(autouse=True)
def _clear(monkeypatch):
    for key in (
        "OAP_POD_PROVIDER_ID",
        "OAP_POD_PROVIDER_BASE_URL",
        "OAP_POD_PROVIDER_ALLOWED_HOST",
        "OAP_POD_PROVIDER_TOKEN",
        "OAP_POD_PROVIDER_EXECUTION_ENABLED",
    ):
        monkeypatch.delenv(key, raising=False)


def _configure(monkeypatch):
    monkeypatch.setenv("OAP_POD_PROVIDER_ID", "printful")
    monkeypatch.setenv("OAP_POD_PROVIDER_BASE_URL", "https://api.printful.com")
    monkeypatch.setenv("OAP_POD_PROVIDER_ALLOWED_HOST", "api.printful.com")
    monkeypatch.setenv("OAP_POD_PROVIDER_TOKEN", "secret-token")
    monkeypatch.setenv("OAP_POD_PROVIDER_EXECUTION_ENABLED", "true")


def test_status_reports_bearer_and_blocks_confirmation(monkeypatch):
    _configure(monkeypatch)
    status = printful_pod_adapter.status()

    assert status["adapter"] == "printful"
    assert status["auth_scheme"] == "Bearer"
    assert status["configuration_complete"] is True
    assert status["draft_order_create_supported"] is True
    assert status["automatic_fulfilment_confirmation"] is False
    assert status["charge_triggering_confirmation_blocked"] is True
    assert status["secret_values_exposed"] is False


def test_execution_disabled_by_default():
    with pytest.raises(printful_pod_adapter.PrintfulAdapterError, match="printful_execution_disabled"):
        printful_pod_adapter.create_draft_order(
            payload={"recipient": {}, "items": []},
            idempotency_key="12345678",
        )


def test_wrong_host_fails_closed(monkeypatch):
    _configure(monkeypatch)
    monkeypatch.setenv("OAP_POD_PROVIDER_BASE_URL", "https://evil.example")
    monkeypatch.setenv("OAP_POD_PROVIDER_ALLOWED_HOST", "evil.example")

    with pytest.raises(printful_pod_adapter.PrintfulAdapterError, match="printful_host_not_allowed"):
        printful_pod_adapter.status()


def test_create_order_never_confirms(monkeypatch):
    _configure(monkeypatch)
    observed = {}

    def fake_request(path, *, method, payload=None):
        observed.update({"path": path, "method": method, "payload": payload})
        return {"code": 200, "result": {"id": 12345, "status": "draft"}}

    monkeypatch.setattr(printful_pod_adapter, "_json_request", fake_request)
    receipt = printful_pod_adapter.create_draft_order(
        payload={
            "recipient": {"name": "Test"},
            "items": [{"variant_id": 1, "quantity": 1}],
        },
        idempotency_key="oap-test-123",
    )

    assert observed["path"] == "/orders"
    assert observed["method"] == "POST"
    assert "confirm" not in observed["path"]
    assert receipt["provider_id"] == "printful"
    assert receipt["order_created"] is True
    assert receipt["order_confirmed"] is False
    assert receipt["fulfilment_started"] is False
    assert receipt["charge_triggering_confirmation_blocked"] is True


def test_confirmation_is_not_exposed():
    with pytest.raises(
        printful_pod_adapter.PrintfulAdapterError,
        match="printful_confirmation_requires_explicit_separate_authority",
    ):
        printful_pod_adapter.confirm_order()
