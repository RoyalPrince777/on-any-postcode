from __future__ import annotations

from mission_control import autonomy_levels, organism_runtime, organism_worker


def test_a3_defaults_to_bounded_pre_authorised_pilot(monkeypatch):
    monkeypatch.delenv("OAP_AUTONOMY_LEVEL", raising=False)
    assert autonomy_levels.configured_level() == "A3"
    decision = autonomy_levels.evaluate_runtime_job("RUNTIME_HEARTBEAT")
    assert decision["allowed"] is True
    assert decision["pre_authorised"] is True
    assert decision["consequential_action_allowed"] is False
    assert decision["human_authority_final"] is True


def test_a2_can_still_be_explicitly_selected(monkeypatch):
    monkeypatch.setenv("OAP_AUTONOMY_LEVEL", "A2")
    decision = autonomy_levels.evaluate_runtime_job("RUNTIME_HEARTBEAT")
    assert decision["allowed"] is False
    assert decision["reason"] == "bounded_runtime_autonomy_not_enabled"


def test_invalid_autonomy_configuration_fails_closed_to_a2(monkeypatch):
    monkeypatch.setenv("OAP_AUTONOMY_LEVEL", "A9")
    assert autonomy_levels.configured_level() == "A2"
    assert autonomy_levels.evaluate_runtime_job("RUNTIME_HEARTBEAT")["allowed"] is False


def test_a3_and_a4_share_only_existing_nonconsequential_runtime_actions(monkeypatch):
    assert autonomy_levels.A3_PILOT_ACTIONS == organism_runtime.ALLOWED_JOB_TYPES
    assert set(organism_worker.HANDLERS) == set(autonomy_levels.A3_PILOT_ACTIONS)
    for level in ("A3", "A4"):
        monkeypatch.setenv("OAP_AUTONOMY_LEVEL", level)
        for action_type in autonomy_levels.A3_PILOT_ACTIONS:
            decision = autonomy_levels.evaluate_runtime_job(action_type)
            assert decision["allowed"] is True
            assert decision["reversible_required"] is True
            assert decision["audit_required"] is True
            assert decision["fail_closed"] is True
            assert decision["consequential_action_allowed"] is False


def test_a4_enables_supervised_workflow_without_expanding_authority(monkeypatch):
    monkeypatch.setenv("OAP_AUTONOMY_LEVEL", "A4")
    workflow = autonomy_levels.evaluate_a4_workflow(
        ["RUNTIME_HEARTBEAT", "RUNTIME_HEALTH_PROBE", "RUNTIME_HEARTBEAT"]
    )
    assert workflow["allowed"] is True
    assert workflow["checkpoint_every"] == 3
    assert workflow["max_steps"] == 21
    assert workflow["supervision_required"] is True
    assert workflow["dynamic_permission_expansion_allowed"] is False
    assert workflow["consequential_action_allowed"] is False


def test_a4_workflow_rejects_unsupervised_unknown_or_oversized_work(monkeypatch):
    monkeypatch.setenv("OAP_AUTONOMY_LEVEL", "A4")
    assert autonomy_levels.evaluate_a4_workflow(
        ["RUNTIME_HEARTBEAT"], supervised=False
    )["allowed"] is False
    assert autonomy_levels.evaluate_a4_workflow(["DEPLOY_PRODUCTION"])["allowed"] is False
    assert autonomy_levels.evaluate_a4_workflow(
        ["RUNTIME_HEARTBEAT"] * 22
    )["allowed"] is False


def test_high_impact_domains_and_a5_remain_locked(monkeypatch):
    monkeypatch.setenv("OAP_AUTONOMY_LEVEL", "A4")
    status = autonomy_levels.status()
    assert status["a3_policy_ready"] is True
    assert status["a3_execution_enabled"] is True
    assert status["a4_policy_ready"] is True
    assert status["a4_enabled"] is True
    assert status["a4_expands_action_authority"] is False
    assert status["a5_enabled"] is False
    assert status["consequential_action_allowed"] is False
    assert status["self_permission_change_allowed"] is False
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
        "self_permission_change",
        "self_constitution_change",
    } <= set(status["forbidden_domains"])
