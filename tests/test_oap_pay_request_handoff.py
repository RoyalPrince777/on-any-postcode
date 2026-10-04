import pytest

from mission_control import oap_pay_request_handoff, sika_account_engine


def _request():
    return {
        "request_id": "req-1",
        "payee_reference": "merchant-1",
        "amount": "12.50",
        "currency": "GBP",
        "jurisdiction": "United Kingdom",
        "surface": "OAP Market",
        "status": "OPEN",
        "expired": False,
        "payable": True,
        "recipient_approval_required": True,
        "creates_debt": False,
    }


def _account():
    return sika_account_engine.BankAccount(
        account_id="acct-1",
        owner_reference="owner-1",
        legal_entity="ON ANY POSTCODE LTD",
        currency="GBP",
        jurisdiction="United Kingdom",
        ledger_account_id="ledger-1",
        status="OPEN",
    )


def test_build_handoff_binds_request_atomically_and_never_authorises(monkeypatch):
    created = {}

    def create_atomic(**kwargs):
        created.update(kwargs)
        return {
            "payment_id": kwargs["payment_id"],
            "hold_id": kwargs["hold_id"],
            "idempotency_key": kwargs["idempotency_key"],
            "payer_account_id": kwargs["payer_account"].account_id,
            "payee_reference": kwargs["payee_reference"],
            "amount": "12.50",
            "currency": kwargs["currency"],
            "jurisdiction": kwargs["jurisdiction"],
            "payment_status": "DRAFT",
            "hold_status": "ACTIVE",
            "customer_authority_receipt": {
                "receipt_hash": "a" * 64,
                "payment_id": kwargs["payment_id"],
            },
            "atomic": True,
            "money_movement": False,
        }

    monkeypatch.setattr(
        oap_pay_request_handoff.sika_atomic_payment,
        "create",
        create_atomic,
    )

    result = oap_pay_request_handoff.build_handoff(
        request=_request(),
        payer_account=_account(),
        payment_id="pay-1",
        idempotency_key="idem-1",
        authority_reference="customer-confirmation-1",
        authorised_at="2026-10-03T08:00:00Z",
        expires_at="2026-10-03T09:00:00Z",
    )
    assert result["payment_intent"]["status"] == "DRAFT"
    assert result["payment_hold"]["status"] == "ACTIVE"
    assert result["payment_hold"]["hold_id"] == "hold:pay-1"
    assert result["request_binding"]["payee_reference"] == "merchant-1"
    assert result["request_binding"]["amount"] == "12.50"
    assert result["request_binding"]["currency"] == "GBP"
    assert result["request_binding"]["jurisdiction"] == "United Kingdom"
    assert result["ready_for_rights_gate"] is True
    assert result["ready_for_sika_pay_gateway"] is False
    assert result["authorised_transition_performed"] is False
    assert result["provider_calling"] is False
    assert result["money_movement"] is False
    assert created["payee_reference"] == "merchant-1"
    assert created["hold_id"] == "hold:pay-1"


def test_build_handoff_rejects_cancelled_or_expired_request():
    request = _request()
    request["status"] = "CANCELLED"
    request["payable"] = False
    with pytest.raises(oap_pay_request_handoff.PaymentRequestHandoffError):
        oap_pay_request_handoff.build_handoff(
            request=request,
            payer_account=_account(),
            payment_id="pay-1",
            idempotency_key="idem-1",
            authority_reference="ref",
            authorised_at="2026-10-03T08:00:00Z",
            expires_at="2026-10-03T09:00:00Z",
        )


def test_verify_binding_detects_request_drift():
    request = _request()
    handoff = {
        "request_binding": {
            "payee_reference": "merchant-1",
            "amount": "12.50",
            "currency": "GBP",
            "jurisdiction": "United Kingdom",
        }
    }
    assert oap_pay_request_handoff.verify_binding(
        handoff=handoff,
        request=request,
    )["verified"] is True
    request["amount"] = "99.00"
    result = oap_pay_request_handoff.verify_binding(
        handoff=handoff,
        request=request,
    )
    assert result["verified"] is False
    assert result["reason"] == "request_binding_mismatch:amount"


def test_status_truth_boundaries():
    status = oap_pay_request_handoff.status()
    assert status["binds_open_request_to_payer"] is True
    assert status["creates_draft_payment_intent"] is True
    assert status["creates_customer_authority_receipt"] is True
    assert status["persists_customer_authority_receipt"] is True
    assert status["creates_payment_hold"] is True
    assert status["atomic_payment_creation"] is True
    assert status["direct_authorisation"] is False
    assert status["provider_calling"] is False
    assert status["money_movement"] is False
