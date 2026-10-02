import json

from flask import Flask

from mission_control import (
    market_sika_pod_runtime,
    product_core_views,
    sika_secure_provider_runtime,
)


def test_provider_execution_routes_are_registered():
    app = Flask(__name__)
    app.register_blueprint(product_core_views.bp, url_prefix="/mission/organs")
    rules = {rule.rule: rule.methods for rule in app.url_map.iter_rules()}

    assert "/mission/organs/market/payments/<payment_id>/provider-submit" in rules
    assert "/mission/organs/market/pod/orders/<order_id>/provider-submit" in rules
    assert "/mission/organs/market/provider/payment/webhook" in rules
    assert "/mission/organs/market/provider/pod/webhook" in rules
    assert "POST" in rules[
        "/mission/organs/market/payments/<payment_id>/provider-submit"
    ]


def test_webhook_header_names_are_configurable_without_exposing_secrets(monkeypatch):
    monkeypatch.setenv(
        "OAP_PAYMENT_PROVIDER_WEBHOOK_TIMESTAMP_HEADER",
        "X-Private-Time",
    )
    monkeypatch.setenv(
        "OAP_PAYMENT_PROVIDER_WEBHOOK_SIGNATURE_HEADER",
        "X-Private-Signature",
    )
    headers = sika_secure_provider_runtime.webhook_header_names("payment")
    assert headers == {
        "timestamp": "X-Private-Time",
        "signature": "X-Private-Signature",
    }
    assert "TOKEN" not in json.dumps(headers).upper()


def test_payment_webhook_normalizes_common_settlement_and_failure_states():
    paid = sika_secure_provider_runtime.normalize_webhook_event(
        kind="payment",
        payload={"provider_reference": "pay-123", "status": "paid"},
    )
    assert paid["provider_state"] == "SETTLED"

    failed = sika_secure_provider_runtime.normalize_webhook_event(
        kind="payment",
        payload={"provider_reference": "pay-123", "status": "declined"},
    )
    assert failed["provider_state"] == "FAILED"


def test_pod_webhook_normalizes_provider_states_and_preserves_signed_metadata():
    event = sika_secure_provider_runtime.normalize_webhook_event(
        kind="pod",
        payload={
            "provider_reference": "pod-123",
            "status": "production",
            "metadata": {"order_id": "order-1"},
        },
    )
    assert event["provider_state"] == "IN_PRODUCTION"
    assert event["metadata"]["order_id"] == "order-1"
    assert (
        market_sika_pod_runtime.distribution_transition_for_supplier_state(
            event["provider_state"]
        )
        == "HANDED_OFF"
    )


def test_provider_webhook_rejects_missing_reference():
    try:
        sika_secure_provider_runtime.normalize_webhook_event(
            kind="payment",
            payload={"status": "paid"},
        )
    except sika_secure_provider_runtime.SecureProviderError as exc:
        assert str(exc) == "provider_reference_missing"
    else:
        raise AssertionError("missing provider reference must fail closed")


def test_provider_execution_source_keeps_required_truth_gates():
    source = open(product_core_views.__file__, encoding="utf-8").read()
    assert 'intent.status != "AUTHORISED"' in source
    assert 'payment.status != "SETTLED"' in source
    assert 'distribution["state"] != "ROUTED"' in source
    assert "verify_webhook(" in source
    assert 'signature_verified") is not True' in source
    assert "delivery_destination_required" in source
