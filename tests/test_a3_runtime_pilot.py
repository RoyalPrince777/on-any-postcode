from __future__ import annotations

from mission_control import autonomy_levels, organism_runtime, organism_worker


def test_a3_defaults_to_bounded_pre_authorised_pilot(monkeypatch):
    monkeypatch.delenv("OAP_AUTONOMY_LEVEL", raising=False)
    assert autonomy_levels.configured_level() == "A3"
    decision = autonomy_levels.evaluate_a3_runtime_job("RUNTIME_HEARTBEAT")
    assert decision["allowed"] is True
    assert decision["pre_authorised"] is True
    assert decision["consequential_action_allowed"] is False
    assert decision["human_authority_final"] is True


def test_a2_can_still_be_explicitly_selected(monkeypatch):
    monkeypatch.setenv("OAP_AUTONOMY_LEVEL", "A2")
    decision = autonomy_levels.evaluate_a3_runtime_job("RUNTIME_HEARTBEAT")
    assert decision["allowed"] is False
    assert decision["reason"] == "a3_not_enabled"
    assert decision["human_authority_final"] is True


def test_invalid_autonomy_configuration_fails_closed_to_a2(monkeypatch):
    monkeypatch.setenv("OAP_AUTONOMY_LEVEL", "A9")
    assert autonomy_levels.configured_level() == "A2"
    decision = autonomy_levels.evaluate_a3_runtime_job("RUNTIME_HEARTBEAT")
    assert decision["allowed"] is False
    assert decision["reason"] == "a3_not_enabled"


def test_a3_pilot_allows_only_existing_nonconsequential_runtime_jobs(monkeypatch):
    monkeypatch.setenv("OAP_AUTONOMY_LEVEL", "A3")
    assert autonomy_levels.A3_PILOT_ACTIONS == organism_runtime.ALLOWED_JOB_TYPES
    assert set(organism_worker.HANDLERS) == set(autonomy_levels.A3_PILOT_ACTIONS)
    for action_type in autonomy_levels.A3_PILOT_ACTIONS:
        decision = autonomy_levels.evaluate_a3_runtime_job(action_type)
        assert decision["allowed"] is True
        assert decision["pre_authorised"] is True
        assert decision["reversible_required"] is True
        assert decision["audit_required"] is True
        assert decision["fail_closed"] is True


def test_a3_rejects_unknown_or_consequential_expansion(monkeypatch):
    monkeypatch.setenv("OAP_AUTONOMY_LEVEL", "A3")
    for action_type in (
        "DEPLOY_PRODUCTION",
        "MIGRATE_DATABASE",
        "TRANSFER_SIKA",
        "CHANGE_AUTH",
        "DISPATCH_RIDER",
        "PUBLISH_PUBLIC_POST",
    ):
        decision = autonomy_levels.evaluate_a3_runtime_job(action_type)
        assert decision["allowed"] is False
        assert decision["reason"] == "action_not_a3_allowlisted"


def test_a4_a5_and_high_impact_domains_remain_locked(monkeypatch):
    monkeypatch.setenv("OAP_AUTONOMY_LEVEL", "A3")
    status = autonomy_levels.status()
    assert status["a3_policy_ready"] is True
    assert status["a3_execution_enabled"] is True
    assert status["a4_enabled"] is False
    assert status["a5_enabled"] is False
    assert status["consequential_action_allowed"] is False
    assert status["human_authority_final"] is True
    assert {
        "money_or_value_transfer",
        "destructive_data_change",
        "production_database_migration",
        "identity_or_permission_change",
        "security_or_auth_change",
        "real_world_dispatch",
        "public_publishing",
        "unreviewed_code_deploy",
    } <= set(status["forbidden_domains"])
