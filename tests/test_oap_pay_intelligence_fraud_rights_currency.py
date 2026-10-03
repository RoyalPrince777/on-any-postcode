from mission_control import (
    oap_pay_intelligence,
    sika_human_rights,
    sika_rights_decision_record,
)


def _rights_record(**overrides):
    base = {
        "action": "payment_hold",
        "authority_reference": "policy:pay:1",
        "evidence_reference": "evidence:pay:1",
        "scope": "single-payment",
        "duration": "transaction-only",
        "explanation_reference": "notice:pay:1",
        "remedy_reference": "appeal:pay:1",
        "recorded_at": "2026-10-03T06:00:00Z",
        "rights": {key: True for key in sika_human_rights.RIGHTS_DIMENSIONS},
        "less_restrictive_option_considered": True,
        "human_review_required": True,
        "human_approved": True,
    }
    base.update(overrides)
    return sika_rights_decision_record.build_decision_record(base)


def test_fraud_intelligence_recommends_review_without_determining_guilt():
    result = oap_pay_intelligence.fraud_intelligence(
        {
            "duplicate_submission": True,
            "account_mismatch": False,
            "payment_mismatch": False,
            "customer_authority_missing": False,
            "rights_not_allow": False,
        }
    )
    assert result["recommended_action"] == "REVIEW"
    assert result["guilt_determined"] is False
    assert result["automatic_confiscation"] is False
    assert result["automatic_permanent_blacklist"] is False
    assert result["execution_granted"] is False


def test_rights_remedy_intelligence_requires_verified_record_and_preserves_remedy():
    record = _rights_record()
    result = oap_pay_intelligence.rights_remedy_intelligence(record)
    assert result["valid"] is True
    assert result["decision"] == "ALLOW"
    assert result["execution_ready"] is True
    assert result["remedy_available"] is True
    assert result["automatic_confiscation"] is False
    assert result["automatic_permanent_blacklist"] is False
    assert result["execution_granted"] is False


def test_rights_remedy_intelligence_rejects_tampered_record():
    record = _rights_record()
    record["scope"] = "all-payments"
    result = oap_pay_intelligence.rights_remedy_intelligence(record)
    assert result["valid"] is False
    assert result["execution_ready"] is False
    assert result["execution_granted"] is False


def test_currency_sika_intelligence_never_invents_convertibility_or_balance():
    result = oap_pay_intelligence.currency_sika_intelligence()
    assert result["valid"] is True
    assert result["name"] == "SIKA"
    assert result["subunit"] == "SEEDS"
    assert result["subunits_per_unit"] == 100
    assert result["recognition_to_fiat_enabled"] is False
    assert result["recognition_to_currency_enabled"] is False
    assert result["fiat_to_currency_enabled"] is False
    assert result["rewards_are_money"] is False
    assert result["legal_tender"] is False
    assert result["balance_known"] is False
    assert result["conversion_rate_claimed"] is False
    assert result["issuance_enabled"] is False
    assert result["money_movement"] is False


def test_status_marks_new_intelligence_built_only():
    status = oap_pay_intelligence.status()
    assert status["fraud_intelligence"] is True
    assert status["rights_remedy_intelligence"] is True
    assert status["currency_sika_intelligence"] is True
    assert status["liquidity_intelligence"] is False
    assert status["guardian_intelligence"] is False
    assert status["smi_pay_intelligence"] is False
