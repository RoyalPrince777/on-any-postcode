from mission_control import sika_alm_forecasting_intelligence, sika_treasury_controls


def _treasury():
    return sika_treasury_controls.snapshot(
        available_sika="1000",
        committed_sika="200",
        tax_reserved_sika="100",
        operating_reserve_sika="200",
    )


def test_healthy_alm_forecast_stays_covered():
    result = sika_alm_forecasting_intelligence.forecast(
        treasury=_treasury(),
        maturity_buckets=[
            sika_alm_forecasting_intelligence.bucket(
                label="0-7d",
                inflows_sika="150",
                outflows_sika="100",
            ),
            sika_alm_forecasting_intelligence.bucket(
                label="8-30d",
                inflows_sika="100",
                outflows_sika="50",
            ),
        ],
        largest_outflow_share_percent="40",
    )
    assert result.maturity_pressure_state == "COVERED"
    assert result.reserve_trajectory_state == "IMPROVING"
    assert result.concentration_state == "DIVERSIFIED"
    assert result.human_review_required is False
    assert result.treasury_action_authorised is False
    assert result.money_moved is False


def test_declining_liquidity_requires_review():
    result = sika_alm_forecasting_intelligence.forecast(
        treasury=_treasury(),
        maturity_buckets=[
            sika_alm_forecasting_intelligence.bucket(
                label="0-7d",
                inflows_sika="0",
                outflows_sika="250",
            ),
        ],
        largest_outflow_share_percent="60",
    )
    assert result.reserve_trajectory_state == "DECLINING"
    assert result.concentration_state == "WATCH"
    assert result.human_review_required is True


def test_projected_shortfall_is_flagged():
    result = sika_alm_forecasting_intelligence.forecast(
        treasury=_treasury(),
        maturity_buckets=[
            sika_alm_forecasting_intelligence.bucket(
                label="0-7d",
                inflows_sika="0",
                outflows_sika="600",
            ),
        ],
    )
    assert result.maturity_pressure_state == "SHORTFALL"
    assert result.minimum_projected_liquidity_sika < 0
    assert result.human_review_required is True


def test_status_keeps_alm_non_executing():
    status = sika_alm_forecasting_intelligence.status()
    assert status["first_party"] is True
    assert status["hedge_execution"] is False
    assert status["treasury_action_authority"] is False
    assert status["money_movement"] is False
