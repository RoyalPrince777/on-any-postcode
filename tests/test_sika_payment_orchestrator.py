import pytest

from mission_control import sika_account_engine, sika_payment_orchestrator


def _account(status="OPEN"):
    return sika_account_engine.BankAccount(
        account_id="acct-777",
        owner_reference="owner-777",
        legal_entity="Europa Crown Bank",
        jurisdiction="United Kingdom",
        currency="GBP",
        ledger_account_id="ledger-777",
        status=status,
    )


def test_schema_contains_durable_idempotency_and_state_constraints():
    sql = "\n".join(sika_payment_orchestrator.SCHEMA_STATEMENTS)
    assert "idempotency_key TEXT NOT NULL UNIQUE" in sql
    assert "payer_account_id TEXT NOT NULL" in sql
    assert "'DRAFT','REVIEW','AUTHORISED','SUBMITTED'" in sql
    assert "'SETTLED','FAILED','CANCELLED'" in sql


def test_payment_intent_flags_authorised_state_for_submission_only():
    authorised = sika_payment_orchestrator.PaymentIntent(
        payment_id="pay-1",
        idempotency_key="idem-1",
        payer_account_id="acct-1",
        payee_reference="payee-1",
        amount=sika_payment_orchestrator.Decimal("10.00"),
        currency="GBP",
        jurisdiction="United Kingdom",
        status="AUTHORISED",
    )
    draft = sika_payment_orchestrator.PaymentIntent(
        payment_id="pay-2",
        idempotency_key="idem-2",
        payer_account_id="acct-1",
        payee_reference="payee-1",
        amount=sika_payment_orchestrator.Decimal("10.00"),
        currency="GBP",
        jurisdiction="United Kingdom",
        status="DRAFT",
    )
    assert authorised.may_submit_to_provider is True
    assert draft.may_submit_to_provider is False


def test_closed_or_frozen_account_cannot_start_payment(monkeypatch):
    for state in ("FROZEN", "CLOSED"):
        with pytest.raises(
            sika_payment_orchestrator.PaymentOrchestratorError,
            match="payer_account_not_open",
        ):
            sika_payment_orchestrator.create_intent(
                payment_id=f"pay-{state}",
                idempotency_key=f"idem-{state}",
                payer_account=_account(state),
                payee_reference="payee",
                amount="10",
                currency="GBP",
                jurisdiction="United Kingdom",
            )


def test_currency_and_jurisdiction_must_match_payer_account():
    with pytest.raises(
        sika_payment_orchestrator.PaymentOrchestratorError,
        match="payer_currency_mismatch",
    ):
        sika_payment_orchestrator.create_intent(
            payment_id="pay-currency",
            idempotency_key="idem-currency",
            payer_account=_account(),
            payee_reference="payee",
            amount="10",
            currency="GHS",
            jurisdiction="United Kingdom",
        )

    with pytest.raises(
        sika_payment_orchestrator.PaymentOrchestratorError,
        match="payer_jurisdiction_mismatch",
    ):
        sika_payment_orchestrator.create_intent(
            payment_id="pay-jurisdiction",
            idempotency_key="idem-jurisdiction",
            payer_account=_account(),
            payee_reference="payee",
            amount="10",
            currency="GBP",
            jurisdiction="Ghana",
        )


def test_status_keeps_payment_orchestrator_non_executing():
    status = sika_payment_orchestrator.status()
    assert status["persistent_payment_intent"] is True
    assert status["provider_calling"] is False
    assert status["journal_posting"] is False
    assert status["settlement_execution"] is False
    assert status["money_movement"] is False



def test_gateway_authorization_contract_requires_exact_truth_boundaries():
    valid = {
        "transition_authorized": True,
        "target_status": "AUTHORISED",
        "provider_calling": False,
        "settlement_execution": False,
        "money_movement": False,
        "human_authority_final": True,
    }
    assert sika_payment_orchestrator._gateway_authorization_valid(valid) is True
    assert sika_payment_orchestrator._gateway_authorization_valid(None) is False

    tampered = dict(valid)
    tampered["money_movement"] = True
    assert sika_payment_orchestrator._gateway_authorization_valid(tampered) is False


def test_authorisation_transition_requires_sika_pay_gateway(monkeypatch):
    current = sika_payment_orchestrator.PaymentIntent(
        payment_id="pay-gated",
        idempotency_key="idem-gated",
        payer_account_id="acct-1",
        payee_reference="payee-1",
        amount=sika_payment_orchestrator.Decimal("10.00"),
        currency="GBP",
        jurisdiction="United Kingdom",
        status="REVIEW",
    )
    monkeypatch.setattr(
        sika_payment_orchestrator,
        "read_intent",
        lambda payment_id: current,
    )
    with pytest.raises(
        sika_payment_orchestrator.PaymentOrchestratorError,
        match="sika_pay_gateway_authorization_required",
    ):
        sika_payment_orchestrator.transition(
            payment_id="pay-gated",
            target_status="AUTHORISED",
        )


def test_status_reports_direct_authorisation_bypass_closed():
    status = sika_payment_orchestrator.status()
    assert status["sika_pay_gateway_required_for_authorisation"] is True
    assert status["direct_authorisation_bypass_allowed"] is False
