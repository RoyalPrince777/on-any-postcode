import pytest

from mission_control import (
    sika_customer_payment_authority,
    sika_human_rights,
    sika_pay_gateway,
    sika_rights_decision_record,
)


def _authority(payment_id, payer_account_id, payee_reference, amount, currency, jurisdiction):
    return sika_customer_payment_authority.build_receipt(
        payment_id=payment_id,
        payer_account_id=payer_account_id,
        payee_reference=payee_reference,
        amount=amount,
        currency=currency,
        jurisdiction=jurisdiction,
        authority_reference="customer-auth:777",
        authorised_at="2026-10-02T18:00:00Z",
        expires_at="2027-10-02T18:00:00Z",
    )


def _rights_record(**overrides):
    base = {
        "action": "payment_hold",
        "authority_reference": "sika:policy:pay:001",
        "evidence_reference": "sika:evidence:pay:123",
        "scope": "single-payment",
        "duration": "transaction-only",
        "explanation_reference": "sika:notice:pay:456",
        "remedy_reference": "sika:appeal:pay:789",
        "recorded_at": "2026-10-02T19:00:00Z",
        "rights": {key: True for key in sika_human_rights.RIGHTS_DIMENSIONS},
        "less_restrictive_option_considered": True,
        "human_review_required": True,
        "human_approved": True,
    }
    base.update(overrides)
    return sika_rights_decision_record.build_decision_record(base)


def test_registered_oap_surface_builds_one_governed_pay_request():
    result = sika_pay_gateway.build_pay_request(
        surface="OAP Market",
        payment_id="pay-777",
        payer_account_id="acct-777",
        payee_reference="merchant-777",
        amount="25",
        currency="gbp",
        jurisdiction="United Kingdom",
        rights_record=_rights_record(),
        customer_authority_receipt=_authority("pay-777", "acct-777", "merchant-777", "25.00", "GBP", "United Kingdom"),
    )
    assert result["ready_for_payment_authorisation"] is True
    assert result["amount"] == "25.00"
    assert result["currency"] == "GBP"
    assert len(result["rights_record_hash"]) == 64
    assert len(result["rights_gate_decision_hash"]) == 64
    assert result["provider_calling"] is False
    assert result["settlement_execution"] is False
    assert result["money_movement"] is False


def test_unregistered_surface_is_rejected():
    with pytest.raises(
        sika_pay_gateway.SikaPayGatewayError,
        match="surface_not_registered",
    ):
        sika_pay_gateway.build_pay_request(
            surface="Random App",
            payment_id="pay-1",
            payer_account_id="acct-1",
            payee_reference="payee-1",
            amount="10",
            currency="GBP",
            jurisdiction="United Kingdom",
            rights_record=_rights_record(),
            customer_authority_receipt=_authority("pay-1", "acct-1", "payee-1", "10.00", "GBP", "United Kingdom"),
        )


def test_review_or_block_rights_record_never_authorises_payment():
    review = _rights_record(human_approved=False)
    result = sika_pay_gateway.build_pay_request(
        surface="OAP Music",
        payment_id="pay-review",
        payer_account_id="acct-1",
        payee_reference="artist-1",
        amount="1",
        currency="GBP",
        jurisdiction="United Kingdom",
        rights_record=review,
        customer_authority_receipt=_authority("pay-review", "acct-1", "artist-1", "1.00", "GBP", "United Kingdom"),
    )
    assert result["ready_for_payment_authorisation"] is False
    assert result["money_movement"] is False


def test_tampered_rights_record_is_rejected():
    record = _rights_record()
    record["scope"] = "all-payments"
    with pytest.raises(
        sika_pay_gateway.SikaPayGatewayError,
        match="rights_record_integrity_failed",
    ):
        sika_pay_gateway.build_pay_request(
            surface="OAP Events",
            payment_id="pay-2",
            payer_account_id="acct-2",
            payee_reference="event-2",
            amount="5",
            currency="GBP",
            jurisdiction="United Kingdom",
            rights_record=record,
            customer_authority_receipt=_authority("pay-2", "acct-2", "event-2", "5.00", "GBP", "United Kingdom"),
        )


def test_only_review_to_authorised_transition_is_exposed():
    request = sika_pay_gateway.build_pay_request(
        surface="OAP World",
        payment_id="pay-3",
        payer_account_id="acct-3",
        payee_reference="payee-3",
        amount="12",
        currency="GBP",
        jurisdiction="United Kingdom",
        rights_record=_rights_record(),
        customer_authority_receipt=_authority("pay-3", "acct-3", "payee-3", "12.00", "GBP", "United Kingdom"),
    )
    allow = sika_pay_gateway.authorize_orchestrator_transition(
        pay_request=request,
        current_status="REVIEW",
    )
    assert allow["transition_authorized"] is True
    assert allow["target_status"] == "AUTHORISED"
    assert allow["payment_id"] == "pay-3"
    assert allow["payer_account_id"] == "acct-3"
    assert allow["payee_reference"] == "payee-3"
    assert allow["amount"] == "12.00"
    assert allow["currency"] == "GBP"
    assert allow["jurisdiction"] == "United Kingdom"
    assert len(allow["rights_record_hash"]) == 64
    assert len(allow["rights_gate_decision_hash"]) == 64
    assert allow["money_movement"] is False

    deny = sika_pay_gateway.authorize_orchestrator_transition(
        pay_request=request,
        current_status="DRAFT",
    )
    assert deny["transition_authorized"] is False


def test_status_truth_boundaries():
    state = sika_pay_gateway.status()
    assert state["single_payment_door"] is True
    assert state["rights_record_required"] is True
    assert state["provider_calling"] is False
    assert state["settlement_execution"] is False
    assert state["money_movement"] is False
    assert state["human_authority_final"] is True



def test_customer_authority_must_match_exact_payment():
    result = sika_pay_gateway.build_pay_request(
        surface="OAP Market",
        payment_id="pay-bind",
        payer_account_id="acct-bind",
        payee_reference="merchant-bind",
        amount="25",
        currency="GBP",
        jurisdiction="United Kingdom",
        rights_record=_rights_record(),
        customer_authority_receipt=_authority(
            "pay-other", "acct-bind", "merchant-bind", "25.00", "GBP", "United Kingdom"
        ),
    )
    assert result["ready_for_payment_authorisation"] is False
    assert result["reason"] == "customer_authority_payment_mismatch"
