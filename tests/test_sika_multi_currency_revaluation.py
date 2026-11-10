import pytest

from mission_control import sika_multi_currency_revaluation


def test_revaluation_calculates_unrealised_gain():
    result = sika_multi_currency_revaluation.revalue(
        source_currency="GHS",
        reporting_currency="GBP",
        source_amount="1000",
        book_rate="0.050",
        closing_rate="0.055",
    )
    assert result.book_value_reporting == 50
    assert result.closing_value_reporting == 55
    assert result.unrealised_fx_gain_loss == 5
    assert result.human_review_required is True
    assert result.fx_executed is False
    assert result.ledger_modified is False
    assert result.money_moved is False


def test_revaluation_calculates_unrealised_loss():
    result = sika_multi_currency_revaluation.revalue(
        source_currency="GBP",
        reporting_currency="GHS",
        source_amount="100",
        book_rate="20",
        closing_rate="19",
    )
    assert result.unrealised_fx_gain_loss == -100
    assert result.human_review_required is True


def test_equal_rates_require_no_review():
    result = sika_multi_currency_revaluation.revalue(
        source_currency="EUR",
        reporting_currency="GBP",
        source_amount="100",
        book_rate="0.85",
        closing_rate="0.85",
    )
    assert result.unrealised_fx_gain_loss == 0
    assert result.human_review_required is False


def test_same_currency_rejected():
    with pytest.raises(
        sika_multi_currency_revaluation.RevaluationError,
        match="currencies_must_differ",
    ):
        sika_multi_currency_revaluation.revalue(
            source_currency="GBP",
            reporting_currency="GBP",
            source_amount="100",
            book_rate="1",
            closing_rate="1",
        )


def test_status_keeps_revaluation_non_executing():
    status = sika_multi_currency_revaluation.status()
    assert status["first_party"] is True
    assert status["fx_execution"] is False
    assert status["ledger_mutation"] is False
    assert status["money_movement"] is False
