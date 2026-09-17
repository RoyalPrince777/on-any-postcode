from mission_control import coherent_automation, distribution_intelligence, live_signals, telemetry


def test_coherent_automation_uses_exact_21_live_signals():
    status = coherent_automation.status()
    assert status["ready"] is True
    assert status["signal_count"] == 21
    assert status["signals_valid"] is True
    assert len(status["signals"]) == 21
    assert status["external_execution_enabled"] is False
    assert status["human_authority_final"] is True


def test_signal_intelligence_monitor_uses_source_timestamped_runtime_evidence(monkeypatch):
    monkeypatch.setattr(
        telemetry,
        "status",
        lambda: {
            "observability_ready": True,
            "local_request_count": 12,
            "local_health_success_count": 4,
            "local_error_count": 1,
            "local_last_request_epoch": 1789616000,
            "local_last_health_success_epoch": 1789615990,
            "last_success_epoch": None,
            "local_fresh_seconds": 300,
            "delivery_verified": False,
        },
    )

    monitor = coherent_automation.operational_monitor()
    observation = monitor["observations"][0]

    assert monitor["name"] == "Signal Intelligence Monitor"
    assert monitor["source_backed"] is True
    assert monitor["registry_is_not_live_evidence"] is True
    assert observation["source"] == "mission_control.telemetry.status"
    assert observation["source_timestamp"].endswith("Z")
    assert observation["freshness"] == "fresh"
    assert observation["signal"]["id"] == "connected"
    assert observation["proof_state"] == "proven"
    assert monitor["execution_allowed"] is False
    assert monitor["human_authority_final"] is True


def test_signal_intelligence_monitor_fails_closed_without_runtime_evidence(monkeypatch):
    monkeypatch.setattr(telemetry, "status", lambda: {})

    monitor = coherent_automation.operational_monitor()
    observation = monitor["observations"][0]

    assert monitor["source_backed"] is False
    assert observation["source_timestamp"] is None
    assert observation["freshness"] == "unseen"
    assert observation["signal"]["id"] == "offline"
    assert observation["proof_state"] == "proof_required"


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
