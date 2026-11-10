import pytest

from mission_control import sika_financial_intelligence, sika_treasury_controls


def test_financial_intelligence_reports_healthy_state():
    treasury = sika_treasury_controls.snapshot(
        available_sika="2000",
        committed_sika="1000",
        tax_reserved_sika="200",
        operating_reserve_sika="200",
    )
    result = sika_financial_intelligence.assess(
        treasury=treasury,
        unreconciled_items=0,
        active_provider_count=3,
        largest_provider_share_percent="40",
        jurisdiction_boundary_breaches=0,
    )
    assert result.liquidity_state == "HEALTHY"
    assert result.reconciliation_state == "CLEAR"
    assert result.provider_concentration_state == "DIVERSIFIED"
    assert result.jurisdiction_isolation_state == "CLEAR"
    assert result.human_review_required is False
    assert result.execution_authorised is False
    assert result.money_moved is False


def test_financial_intelligence_flags_liquidity_shortfall():
    treasury = sika_treasury_controls.snapshot(
        available_sika="900",
        committed_sika="1000",
    )
    result = sika_financial_intelligence.assess(
        treasury=treasury,
        active_provider_count=2,
        largest_provider_share_percent="50",
    )
    assert result.liquidity_state == "SHORTFALL"
    assert result.human_review_required is True


def test_financial_intelligence_flags_reconciliation_exceptions():
    treasury = sika_treasury_controls.snapshot(available_sika="1000")
    result = sika_financial_intelligence.assess(
        treasury=treasury,
        unreconciled_items=6,
        active_provider_count=2,
        largest_provider_share_percent="45",
    )
    assert result.reconciliation_state == "ELEVATED"
    assert result.human_review_required is True


def test_financial_intelligence_flags_provider_concentration():
    treasury = sika_treasury_controls.snapshot(available_sika="1000")
    result = sika_financial_intelligence.assess(
        treasury=treasury,
        active_provider_count=1,
        largest_provider_share_percent="100",
    )
    assert result.provider_concentration_state == "CONCENTRATED"
    assert result.human_review_required is True


def test_financial_intelligence_flags_jurisdiction_breach():
    treasury = sika_treasury_controls.snapshot(available_sika="1000")
    result = sika_financial_intelligence.assess(
        treasury=treasury,
        active_provider_count=2,
        largest_provider_share_percent="40",
        jurisdiction_boundary_breaches=1,
    )
    assert result.jurisdiction_isolation_state == "BREACH"
    assert result.human_review_required is True


def test_financial_intelligence_rejects_invalid_provider_share():
    treasury = sika_treasury_controls.snapshot(available_sika="1000")
    with pytest.raises(
        sika_financial_intelligence.FinancialIntelligenceError,
        match="provider_share_invalid",
    ):
        sika_financial_intelligence.assess(
            treasury=treasury,
            active_provider_count=2,
            largest_provider_share_percent="101",
        )


def test_status_keeps_financial_intelligence_non_executing():
    status = sika_financial_intelligence.status()
    assert status["first_party"] is True
    assert status["predictive_ai_controls_money"] is False
    assert status["execution_authority"] is False
    assert status["money_movement"] is False
