from mission_control import oap_pay_intelligence, sika_treasury_controls


def test_liquidity_intelligence_reads_treasury_without_authorising_execution():
    state = sika_treasury_controls.snapshot(
        available_sika="100.00",
        committed_sika="20.00",
        tax_reserved_sika="10.00",
        operating_reserve_sika="15.00",
    )
    result = oap_pay_intelligence.liquidity_intelligence(state)
    assert result["valid"] is True
    assert result["liquidity_healthy"] is True
    assert result["free_liquidity_sika"] == "55.00"
    assert result["payment_execution_authorised"] is False
    assert result["money_movement"] is False


def test_liquidity_intelligence_surfaces_shortfall():
    state = sika_treasury_controls.snapshot(
        available_sika="10.00",
        committed_sika="20.00",
        tax_reserved_sika="5.00",
        operating_reserve_sika="5.00",
    )
    result = oap_pay_intelligence.liquidity_intelligence(state)
    assert result["valid"] is True
    assert result["liquidity_healthy"] is False
    assert result["shortfall_sika"] == "20.00"
    assert result["may_enter_payment_review"] is False


def test_guardian_intelligence_escalates_rights_or_liquidity_gaps():
    result = oap_pay_intelligence.guardian_intelligence(
        fraud={"valid": True, "recommended_action": "ALLOW_TO_CONTINUE_REVIEW"},
        rights={"valid": True, "execution_ready": False},
        settlement={"valid": True},
        liquidity={"valid": True, "liquidity_healthy": False},
    )
    assert result["valid"] is True
    assert result["recommended_action"] == "REVIEW"
    assert "rights_not_ready" in result["warnings"]
    assert "liquidity_not_healthy" in result["warnings"]
    assert result["automatic_execution"] is False
    assert result["execution_granted"] is False


def test_smi_pay_intelligence_summarises_without_becoming_authority():
    base = {"valid": True}
    guardian = {
        "valid": True,
        "recommended_action": "CONTINUE_REVIEW",
    }
    result = oap_pay_intelligence.smi_pay_intelligence(
        transition=base,
        wallet=base,
        payment=base,
        request=base,
        merchant=base,
        activity=base,
        settlement=base,
        fraud=base,
        rights=base,
        currency=base,
        liquidity=base,
        guardian=guardian,
    )
    assert result["valid"] is True
    assert result["intelligence_blocks_observed"] == 12
    assert result["recommended_action"] == "CONTINUE_REVIEW"
    assert result["execution_authority"] is False
    assert result["provider_calling"] is False
    assert result["money_movement"] is False


def test_smi_pay_intelligence_fails_to_review_on_invalid_component():
    ok = {"valid": True}
    result = oap_pay_intelligence.smi_pay_intelligence(
        transition=ok,
        wallet=ok,
        payment=ok,
        request=ok,
        merchant=ok,
        activity=ok,
        settlement=ok,
        fraud=ok,
        rights={"valid": False},
        currency=ok,
        liquidity=ok,
        guardian={"valid": True, "recommended_action": "CONTINUE_REVIEW"},
    )
    assert result["valid"] is False
    assert result["recommended_action"] == "REVIEW"
    assert result["execution_authority"] is False


def test_status_marks_all_defined_intelligence_blocks_built():
    status = oap_pay_intelligence.status()
    for key in (
        "transition_intelligence",
        "wallet_intelligence",
        "payment_intelligence",
        "request_intelligence",
        "merchant_intelligence",
        "activity_intelligence",
        "settlement_intelligence",
        "fraud_intelligence",
        "rights_remedy_intelligence",
        "currency_sika_intelligence",
        "liquidity_intelligence",
        "guardian_intelligence",
        "smi_pay_intelligence",
    ):
        assert status[key] is True
    assert status["advisory_only"] is True
    assert status["money_movement"] is False
