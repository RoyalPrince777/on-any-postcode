import pytest

from mission_control import sika_financial_model


def test_seven_front_doors_are_unique_and_fail_closed():
    status = sika_financial_model.status()
    assert status["validation"]["passed"] is True
    assert status["validation"]["front_doors"] == 7
    assert status["regulated_execution_enabled"] is False
    assert status["customer_funds_enabled"] is False
    assert status["investment_execution_enabled"] is False
    assert status["custody_execution_enabled"] is False


def test_financial_state_classes_remain_separate():
    classes = {
        item["id"]: item for item in sika_financial_model.LEDGER_CLASSES
    }
    assert set(classes) == {
        "canonical_value",
        "treasury",
        "custody",
        "recognition",
    }
    assert len({item["owner"] for item in classes.values()}) == 4
    assert classes["recognition"]["spendable_claim"] is False
    assert classes["recognition"]["custody_claim"] is False
    assert classes["custody"]["custody_claim"] is True


def test_balance_reference_never_self_promotes_to_money():
    reference = sika_financial_model.balance_reference(
        "canonical_value",
        "100.00 SIKA",
    )
    assert reference.amount_reference == "100.00 SIKA"
    assert reference.spendable is False
    assert reference.money_claim is False


def test_custody_reference_is_not_spendable_cash():
    reference = sika_financial_model.balance_reference(
        "custody",
        "asset-record-001",
    )
    assert reference.custody_claim is True
    assert reference.spendable is False
    assert reference.money_claim is False


def test_unknown_ledger_class_fails_closed():
    with pytest.raises(
        sika_financial_model.OperatingModelError,
        match="unknown_ledger_class",
    ):
        sika_financial_model.balance_reference("mystery", "1")


def test_blank_amount_reference_fails_closed():
    with pytest.raises(
        sika_financial_model.OperatingModelError,
        match="amount_reference_required",
    ):
        sika_financial_model.balance_reference("treasury", "")
