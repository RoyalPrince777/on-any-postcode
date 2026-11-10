from mission_control import sika_fraud_financial_crime_intelligence


def test_low_risk_state_requires_no_review():
    result = sika_fraud_financial_crime_intelligence.assess(
        transactions_last_hour=2,
        baseline_hourly_transactions=2,
        transaction_amount="100",
        baseline_amount="100",
    )
    assert result.risk_level == "LOW"
    assert result.human_review_required is False
    assert result.autonomous_block is False
    assert result.regulatory_report_filed is False
    assert result.money_moved is False


def test_velocity_spike_requires_review():
    result = sika_fraud_financial_crime_intelligence.assess(
        transactions_last_hour=12,
        baseline_hourly_transactions=2,
        transaction_amount="100",
        baseline_amount="100",
    )
    assert result.velocity_state == "SPIKE"
    assert result.risk_level == "REVIEW"
    assert result.human_review_required is True


def test_amount_anomaly_requires_review():
    result = sika_fraud_financial_crime_intelligence.assess(
        transactions_last_hour=1,
        baseline_hourly_transactions=1,
        transaction_amount="500",
        baseline_amount="100",
    )
    assert result.amount_state == "ANOMALOUS"
    assert result.human_review_required is True


def test_multiple_signals_raise_high_risk_without_autonomous_block():
    result = sika_fraud_financial_crime_intelligence.assess(
        transactions_last_hour=20,
        baseline_hourly_transactions=2,
        transaction_amount="1000",
        baseline_amount="100",
        failed_settlements_24h=4,
        jurisdiction_mismatch=True,
        provider_reference_reused=True,
        reconciliation_exception=True,
    )
    assert result.risk_level == "HIGH"
    assert result.human_review_required is True
    assert result.autonomous_block is False
    assert result.regulatory_report_filed is False


def test_status_keeps_fraud_intelligence_non_executing():
    status = sika_fraud_financial_crime_intelligence.status()
    assert status["first_party"] is True
    assert status["autonomous_blocking"] is False
    assert status["regulatory_reporting_execution"] is False
    assert status["ledger_mutation"] is False
    assert status["money_movement"] is False
