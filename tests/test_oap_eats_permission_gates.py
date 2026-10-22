"""HTTP guards and early payment denials; PostgreSQL cases prove durable writes."""
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from mission_control import (
    oap_eats_fulfilment,
    oap_eats_routes,
    oap_eats_store,
    sika_account_engine,
)

CUSTOMER = "11111111-1111-4111-8111-111111111111"
OUTSIDER = "22222222-2222-4222-8222-222222222222"
ORDER = "33333333-3333-4333-8333-333333333333"
PATHS = ["/eats/orders", *[f"/eats/orders/{ORDER}/{suffix}" for suffix in ("state", "payment", "delivery")]]


@pytest.mark.parametrize("path", PATHS)
def test_writes_require_authenticated_session(anonymous_client, path):
    assert anonymous_client.post(path, json={}).status_code == 401


@pytest.mark.parametrize("path", PATHS)
def test_writes_require_csrf(client, path):
    response = client.post(path, json={})
    assert response.status_code == 403
    assert response.get_json()["error"]["code"] == "csrf_failed"


@pytest.mark.parametrize("path", PATHS)
def test_write_rate_limit_precedes_all_service_calls(client, csrf, monkeypatch, path):
    monkeypatch.setattr(oap_eats_routes.web_security.PUBLIC_WRITE_LIMITER, "allow", lambda _: False)
    state, payment, delivery, create = Mock(), Mock(), Mock(), Mock()
    monkeypatch.setattr(oap_eats_store.STORE, "create_order", create)
    monkeypatch.setattr(oap_eats_store.STORE, "transition", state)
    monkeypatch.setattr(oap_eats_fulfilment, "bind_payment", payment)
    monkeypatch.setattr(oap_eats_fulfilment, "create_delivery", delivery)
    response = client.post(path, json={}, headers={"X-OAP-CSRF": csrf["csrf_token"]})
    assert response.status_code == 429
    for service in (state, payment, delivery, create):
        service.assert_not_called()


def test_non_customer_is_denied_before_payment_evidence_is_read(monkeypatch):
    def deny(**_):
        raise PermissionError("order_customer_required")
    monkeypatch.setattr(oap_eats_store.STORE, "require_customer_order", deny)
    intent = Mock()
    monkeypatch.setattr(oap_eats_fulfilment.sika_payment_orchestrator, "read_intent", intent)
    with pytest.raises(PermissionError, match="order_customer_required"):
        oap_eats_fulfilment.bind_payment(order_id=ORDER, customer_identity_id=OUTSIDER, payment_id="pay-1")
    intent.assert_not_called()


def test_order_creation_uses_session_customer_not_payload(client, csrf, monkeypatch):
    create = Mock(side_effect=PermissionError("permission_denied"))
    monkeypatch.setattr(oap_eats_store.STORE, "create_order", create)
    response = client.post(
        "/eats/orders", json={"customer_identity_id": OUTSIDER, "pricing_version": "eats_catalogue_v1"},
        headers={"X-OAP-CSRF": csrf["csrf_token"], "Idempotency-Key": "creation-identity"},
    )
    assert response.status_code == 403
    assert create.call_args.kwargs["customer_identity_id"] == CUSTOMER
    assert "pricing_version" not in create.call_args.kwargs


def test_foreign_payer_is_denied_before_hold_lookup_or_order_write(monkeypatch):
    monkeypatch.setattr(oap_eats_store.STORE, "require_customer_order", lambda **_: {"amount_minor": 1599, "currency": "GBP"})
    monkeypatch.setattr(oap_eats_fulfilment.sika_payment_orchestrator, "read_intent", lambda _: SimpleNamespace(payer_account_id="acct-1"))
    account = sika_account_engine.BankAccount("acct-1", OUTSIDER, "CI fixture", "United Kingdom", "GBP", "ledger-1", "OPEN")
    monkeypatch.setattr(sika_account_engine, "read_account", lambda _: account)
    hold, bind = Mock(), Mock()
    monkeypatch.setattr(oap_eats_fulfilment.sika_payment_reservations, "read_hold", hold)
    monkeypatch.setattr(oap_eats_store.STORE, "bind_payment", bind)
    with pytest.raises(PermissionError, match="payment_payer_not_owned_or_open"):
        oap_eats_fulfilment.bind_payment(order_id=ORDER, customer_identity_id=CUSTOMER, payment_id="pay-1")
    hold.assert_not_called()
    bind.assert_not_called()


@pytest.mark.parametrize("state", ["DRAFT", "REVIEW", "SETTLED", "FAILED", "CANCELLED"])
def test_unusable_intent_state_cannot_claim_capture_or_write(monkeypatch, state):
    monkeypatch.setattr(oap_eats_store.STORE, "require_customer_order", lambda **_: {"amount_minor": 1599, "currency": "GBP"})
    intent = SimpleNamespace(payer_account_id="acct-1", status=state, amount=Decimal("15.99"))
    monkeypatch.setattr(oap_eats_fulfilment.sika_payment_orchestrator, "read_intent", lambda _: intent)
    account = sika_account_engine.BankAccount("acct-1", CUSTOMER, "CI fixture", "United Kingdom", "GBP", "ledger-1", "OPEN")
    monkeypatch.setattr(sika_account_engine, "read_account", lambda _: account)
    hold, bind = Mock(), Mock()
    monkeypatch.setattr(oap_eats_fulfilment.sika_payment_reservations, "read_hold", hold)
    monkeypatch.setattr(oap_eats_store.STORE, "bind_payment", bind)
    with pytest.raises(ValueError, match="payment_intent_not_bindable"):
        oap_eats_fulfilment.bind_payment(order_id=ORDER, customer_identity_id=CUSTOMER, payment_id="pay-1")
    hold.assert_not_called()
    bind.assert_not_called()


@pytest.mark.parametrize("suffix,service_owner,service_name,identity_key", [
    ("state", oap_eats_store.STORE, "transition", "actor_identity_id"),
    ("payment", oap_eats_fulfilment, "bind_payment", "customer_identity_id"),
    ("delivery", oap_eats_fulfilment, "create_delivery", "customer_identity_id"),
])
def test_http_uses_session_identity_and_returns_permission_denial(
    client, csrf, monkeypatch, suffix, service_owner, service_name, identity_key,
):
    service = Mock(side_effect=PermissionError("permission_denied"))
    monkeypatch.setattr(service_owner, service_name, service)
    response = client.post(
        f"/eats/orders/{ORDER}/{suffix}",
        json={"state": "settled", "role": "merchant", "actor_identity_id": OUTSIDER,
              "customer_identity_id": OUTSIDER, "payment_id": "pay-1"},
        headers={"X-OAP-CSRF": csrf["csrf_token"]},
    )
    assert response.status_code == 403
    assert response.get_json()["error"]["code"] == "permission_denied"
    assert service.call_args.kwargs[identity_key] == CUSTOMER
    assert "role" not in service.call_args.kwargs
