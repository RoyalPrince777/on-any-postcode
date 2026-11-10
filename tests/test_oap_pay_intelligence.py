from decimal import Decimal

from mission_control import (
    oap_pay_intelligence,
    sika_account_engine,
    sika_payment_orchestrator,
)


def test_transition_intelligence_rejects_impossible_jump():
    result = oap_pay_intelligence.transition_intelligence(
        current_status="DRAFT",
        target_status="SETTLED",
    )
    assert result["valid"] is False
    assert result["reason"] == "payment_transition_not_allowed"
    assert result["execution_granted"] is False


def test_transition_intelligence_accepts_valid_step_without_executing():
    result = oap_pay_intelligence.transition_intelligence(
        current_status="REVIEW",
        target_status="AUTHORISED",
    )
    assert result["valid"] is True
    assert result["execution_granted"] is False


def test_wallet_intelligence_never_fabricates_balance():
    account = sika_account_engine.BankAccount(
        account_id="acct-1",
        owner_reference="owner-1",
        legal_entity="OAP",
        jurisdiction="United Kingdom",
        currency="GBP",
        ledger_account_id="ledger-1",
        status="OPEN",
    )
    result = oap_pay_intelligence.wallet_intelligence(account)
    assert result["valid"] is True
    assert result["customer_activity_allowed"] is True
    assert result["balance_known"] is False
    assert result["balance_fabricated"] is False
    assert result["money_movement"] is False


def test_payment_intelligence_projects_next_states_only():
    intent = sika_payment_orchestrator.PaymentIntent(
        payment_id="pay-1",
        idempotency_key="idem-1",
        payer_account_id="acct-1",
        payee_reference="merchant-1",
        amount=Decimal("12.00"),
        currency="GBP",
        jurisdiction="United Kingdom",
        status="AUTHORISED",
    )
    result = oap_pay_intelligence.payment_intelligence(intent)
    assert result["valid"] is True
    assert result["next_states"] == ("CANCELLED", "SUBMITTED")
    assert result["may_submit_to_provider"] is True
    assert result["execution_granted"] is False


def test_request_intelligence_requires_recipient_approval_and_creates_no_debt():
    result = oap_pay_intelligence.request_intelligence(
        {
            "request_id": "req-1",
            "requester_reference": "creator-1",
            "recipient_reference": "member-1",
            "amount": "5.00",
            "currency": "GBP",
        }
    )
    assert result["valid"] is True
    assert result["recipient_approval_required"] is True
    assert result["creates_debt"] is False
    assert result["execution_granted"] is False
    assert result["money_movement"] is False


def test_status_is_advisory_and_non_executing():
    status = oap_pay_intelligence.status()
    assert status["transition_intelligence"] is True
    assert status["wallet_intelligence"] is True
    assert status["payment_intelligence"] is True
    assert status["request_intelligence"] is True
    assert status["advisory_only"] is True
    assert status["money_movement"] is False
