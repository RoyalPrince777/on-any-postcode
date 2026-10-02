from decimal import Decimal

import pytest

from mission_control import sika_account_engine, sika_card_controls


def _account(status="OPEN"):
    return sika_account_engine.BankAccount(
        account_id="acct-card",
        owner_reference="owner-card",
        legal_entity="Europa Crown Bank",
        jurisdiction="United Kingdom",
        currency="GBP",
        ledger_account_id="ledger-card",
        status=status,
    )


def test_card_model_only_allows_active_authorisation_review():
    active = sika_card_controls.CardAccount(
        card_id="card-1",
        account_id="acct-card",
        owner_reference="owner-card",
        status="ACTIVE",
        single_transaction_limit=Decimal("100.00"),
        daily_limit=Decimal("500.00"),
    )
    frozen = sika_card_controls.CardAccount(
        card_id="card-1",
        account_id="acct-card",
        owner_reference="owner-card",
        status="FROZEN",
        single_transaction_limit=Decimal("100.00"),
        daily_limit=Decimal("500.00"),
    )
    assert active.may_enter_authorisation_review is True
    assert frozen.may_enter_authorisation_review is False


def test_spending_control_rejects_amount_over_single_transaction_limit():
    card = sika_card_controls.CardAccount(
        card_id="card-1",
        account_id="acct-card",
        owner_reference="owner-card",
        status="ACTIVE",
        single_transaction_limit=Decimal("100.00"),
        daily_limit=Decimal("500.00"),
    )
    assert sika_card_controls.amount_within_controls(card=card, amount="99.99") is True
    assert sika_card_controls.amount_within_controls(card=card, amount="100.01") is False


def test_closed_account_cannot_create_card():
    with pytest.raises(sika_card_controls.CardControlError, match="account_not_open"):
        sika_card_controls.create_card(
            card_id="card-closed",
            account=_account(status="CLOSED"),
        )


def test_status_does_not_claim_live_card_network():
    status = sika_card_controls.status()
    assert status["card_account_binding"] is True
    assert status["spending_controls"] is True
    assert status["live_network_issuing"] is False
    assert status["live_authorisation_processing"] is False
    assert status["scheme_connectivity"] is False
    assert status["money_movement"] is False
