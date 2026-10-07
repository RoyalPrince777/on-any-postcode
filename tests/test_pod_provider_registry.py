from __future__ import annotations

import pytest

from mission_control import (
    pod_provider_registry,
    printful_pod_adapter,
    prodigi_pod_adapter,
)


@pytest.fixture(autouse=True)
def _clear_provider_env(monkeypatch):
    keys = (
        "OAP_POD_PROVIDER_ID",
        "OAP_POD_PROVIDER_BASE_URL",
        "OAP_POD_PROVIDER_ALLOWED_HOST",
        "OAP_POD_PROVIDER_TOKEN",
        "OAP_POD_PROVIDER_EXECUTION_ENABLED",
        "OAP_POD_PRODIGI_BASE_URL",
        "OAP_POD_PRODIGI_ALLOWED_HOST",
        "OAP_POD_PRODIGI_TOKEN",
        "OAP_POD_PRODIGI_EXECUTION_ENABLED",
        "OAP_POD_PRINTFUL_BASE_URL",
        "OAP_POD_PRINTFUL_ALLOWED_HOST",
        "OAP_POD_PRINTFUL_TOKEN",
        "OAP_POD_PRINTFUL_EXECUTION_ENABLED",
    )
    for key in keys:
        monkeypatch.delenv(key, raising=False)


def test_registry_reports_multi_provider_without_secrets():
    status = pod_provider_registry.status()

    assert status["registry"] == "oap_pod_multi_provider"
    assert status["supported_providers"] == ["prodigi", "printful", "tapstitch"]
    assert status["single_global_provider_required"] is False
    assert status["per_order_provider_routing_supported"] is True
    assert status["tapstitch_direct_execution_allowed"] is False
    assert status["secret_values_exposed"] is False


def test_explicit_provider_routes_independently(monkeypatch):
    observed = []

    monkeypatch.setattr(
        prodigi_pod_adapter,
        "submit_order",
        lambda **kwargs: observed.append(("prodigi", kwargs)) or {
            "provider_id": "prodigi",
            "receipt_hash": "p" * 64,
        },
    )
    monkeypatch.setattr(
        printful_pod_adapter,
        "create_draft_order",
        lambda **kwargs: observed.append(("printful", kwargs)) or {
            "provider_id": "printful",
            "receipt_hash": "f" * 64,
        },
    )

    first = pod_provider_registry.submit(
        provider_id="prodigi",
        payload={"items": []},
        idempotency_key="prodigi-12345678",
    )
    second = pod_provider_registry.submit(
        provider_id="printful",
        payload={"items": []},
        idempotency_key="printful-12345678",
    )

    assert first["provider_id"] == "prodigi"
    assert second["provider_id"] == "printful"
    assert [row[0] for row in observed] == ["prodigi", "printful"]


def test_tapstitch_direct_execution_stays_fail_closed():
    with pytest.raises(RuntimeError, match="tapstitch_direct_api_contract_unproven"):
        pod_provider_registry.submit(
            provider_id="tapstitch",
            payload={"items": []},
            idempotency_key="tapstitch-12345678",
        )


def test_unknown_provider_fails_closed():
    with pytest.raises(
        pod_provider_registry.PodProviderRegistryError,
        match="pod_provider_not_supported",
    ):
        pod_provider_registry.submit(
            provider_id="unknown-provider",
            payload={"items": []},
            idempotency_key="unknown-12345678",
        )


def test_prodigi_and_printful_can_be_configured_at_same_time(monkeypatch):
    monkeypatch.setenv("OAP_POD_PRODIGI_BASE_URL", "https://api.sandbox.prodigi.com")
    monkeypatch.setenv("OAP_POD_PRODIGI_ALLOWED_HOST", "api.sandbox.prodigi.com")
    monkeypatch.setenv("OAP_POD_PRODIGI_TOKEN", "prodigi-secret")
    monkeypatch.setenv("OAP_POD_PRODIGI_EXECUTION_ENABLED", "true")

    monkeypatch.setenv("OAP_POD_PRINTFUL_BASE_URL", "https://api.printful.com")
    monkeypatch.setenv("OAP_POD_PRINTFUL_ALLOWED_HOST", "api.printful.com")
    monkeypatch.setenv("OAP_POD_PRINTFUL_TOKEN", "printful-secret")
    monkeypatch.setenv("OAP_POD_PRINTFUL_EXECUTION_ENABLED", "true")

    prodigi = prodigi_pod_adapter.status()
    printful = printful_pod_adapter.status()

    assert prodigi["configuration_complete"] is True
    assert printful["configuration_complete"] is True
    assert "prodigi-secret" not in repr(prodigi)
    assert "printful-secret" not in repr(printful)
