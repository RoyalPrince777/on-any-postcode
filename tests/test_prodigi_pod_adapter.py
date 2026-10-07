from __future__ import annotations

from pathlib import Path

import app as app_module
from mission_control import prodigi_pod_adapter


def _root() -> Path:
    return Path(app_module.app.root_path)


def test_prodigi_status_defaults_fail_closed(monkeypatch):
    for key in (
        "OAP_POD_PROVIDER_ID",
        "OAP_POD_PROVIDER_BASE_URL",
        "OAP_POD_PROVIDER_ALLOWED_HOST",
        "OAP_POD_PROVIDER_TOKEN",
        "OAP_POD_PROVIDER_EXECUTION_ENABLED",
    ):
        monkeypatch.delenv(key, raising=False)

    status = prodigi_pod_adapter.status()
    assert status["adapter"] == "prodigi"
    assert status["execution_enabled"] is False
    assert status["configuration_complete"] is False
    assert status["signed_callback_trusted"] is False
    assert status["status_readback_supported"] is True
    assert status["secret_values_exposed"] is False


def test_prodigi_sandbox_configuration_uses_x_api_key_without_exposing_secret(monkeypatch):
    monkeypatch.setenv("OAP_POD_PROVIDER_ID", "prodigi")
    monkeypatch.setenv("OAP_POD_PROVIDER_BASE_URL", "https://api.sandbox.prodigi.com")
    monkeypatch.setenv("OAP_POD_PROVIDER_ALLOWED_HOST", "api.sandbox.prodigi.com")
    monkeypatch.setenv("OAP_POD_PROVIDER_TOKEN", "sandbox-secret")
    monkeypatch.setenv("OAP_POD_PROVIDER_EXECUTION_ENABLED", "true")

    status = prodigi_pod_adapter.status()
    assert status["configuration_complete"] is True
    assert status["sandbox"] is True
    assert status["live"] is False
    assert status["auth_scheme"] == "X-API-Key"
    assert "sandbox-secret" not in repr(status)


def test_prodigi_submit_normalizes_order_receipt(monkeypatch):
    monkeypatch.setenv("OAP_POD_PROVIDER_BASE_URL", "https://api.sandbox.prodigi.com")
    monkeypatch.setattr(
        prodigi_pod_adapter,
        "_json_request",
        lambda path, method, payload=None: {
            "outcome": "Created",
            "order": {
                "id": "ord_123456",
                "status": {"stage": "InProgress"},
            },
        },
    )
    receipt = prodigi_pod_adapter.submit_order(
        payload={"shippingMethod": "Standard", "recipient": {}, "items": []},
        idempotency_key="oap-pod-12345678",
    )
    assert receipt["provider_id"] == "prodigi"
    assert receipt["provider_reference"] == "ord_123456"
    assert receipt["provider_state"] == "INPROGRESS"
    assert receipt["provider_execution_performed"] is True
    assert receipt["secret_values_exposed"] is False


def test_prodigi_readback_normalizes_status_without_customer_payload(monkeypatch):
    monkeypatch.setattr(
        prodigi_pod_adapter,
        "_json_request",
        lambda path, method, payload=None: {
            "order": {
                "id": "ord_123456",
                "status": {"stage": "Complete"},
                "shipments": [{"id": "shp_1"}],
                "recipient": {"name": "Private Customer"},
            },
        },
    )
    result = prodigi_pod_adapter.get_order(provider_reference="ord_123456")
    assert result == {
        "provider_id": "prodigi",
        "provider_reference": "ord_123456",
        "provider_state": "COMPLETE",
        "shipment_count": 1,
        "readback_performed": True,
        "secret_values_exposed": False,
        "human_authority_final": True,
    }


def test_prodigi_adapter_is_selected_only_for_prodigi_provider_id():
    source = (
        _root() / "mission_control" / "product_core_views.py"
    ).read_text(encoding="utf-8")
    section = source.split('def execute_market_pod(subject_id: str):', 1)[1].split(
        '@bp.post("/market/pod/provider/webhook")', 1
    )[0]

    assert 'os.environ.get("OAP_POD_PROVIDER_ID", "")' in section
    assert 'pod_provider_id == "prodigi"' in section
    assert "prodigi_pod_adapter.submit_order(" in section
    assert "sika_secure_provider_runtime.submit(" in section
    assert "kind=\"pod\"" in section


def test_prodigi_adapter_never_trusts_unsigned_callbacks():
    source = (
        _root() / "mission_control" / "prodigi_pod_adapter.py"
    ).read_text(encoding="utf-8")

    assert '"signed_callback_trusted": False' in source
    assert '"status_readback_supported": True' in source
    assert "X-API-Key" in source
    assert "api.sandbox.prodigi.com" in source
    assert "api.prodigi.com" in source
