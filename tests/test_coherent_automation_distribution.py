from mission_control import coherent_automation, distribution_intelligence, live_signals


def test_coherent_automation_uses_exact_21_live_signals():
    status = coherent_automation.status()
    assert status["ready"] is True
    assert status["signal_count"] == 21
    assert status["signals_valid"] is True
    assert len(status["signals"]) == 21
    assert status["external_execution_enabled"] is False
    assert status["human_authority_final"] is True


def test_coherent_automation_plan_never_self_executes():
    empty = coherent_automation.plan("")
    assert empty["accepted"] is False
    assert empty["execution_allowed"] is False

    plan = coherent_automation.plan("prepare OAP distribution release", target="OAP Distribution")
    assert plan["accepted"] is True
    assert plan["execution_allowed"] is False
    assert plan["human_authority_final"] is True


def test_distribution_requires_proof_before_external_ready():
    status = distribution_intelligence.status()
    assert status["ready"] is True
    assert status["core_signal_count"] == 21
    assert status["external_execution_enabled"] is False

    blocked = distribution_intelligence.review_release({"title": "Release One"})
    assert blocked["owned_oap_distribution_ready"] is False
    assert blocked["external_distribution_ready"] is False
    assert blocked["execution_performed"] is False

    owned = distribution_intelligence.review_release(
        {
            "title": "Release One",
            "rights_proof": True,
            "campaign_ready": True,
            "human_approval": True,
            "receipt_destination": True,
        }
    )
    assert owned["owned_oap_distribution_ready"] is True
    assert owned["external_distribution_ready"] is False

    external = distribution_intelligence.review_release(
        {
            "title": "Release One",
            "rights_proof": True,
            "campaign_ready": True,
            "human_approval": True,
            "receipt_destination": True,
            "external_adapter_proven": True,
        }
    )
    assert external["external_distribution_ready"] is True
    assert external["execution_performed"] is False


def test_live_signal_contract_still_validates():
    validation = live_signals.validate_signal_language()
    assert validation["passed"] is True
    assert validation["signal_count"] == 21
