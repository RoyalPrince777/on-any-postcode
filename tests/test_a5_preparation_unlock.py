from mission_control import autonomy_levels


def test_a5_can_be_enabled_for_preparation_only(monkeypatch):
    monkeypatch.setenv("OAP_A5_ENABLED", "true")
    monkeypatch.setenv("OAP_AUTONOMY_LEVEL", "A5")
    monkeypatch.setattr(autonomy_levels, "A5_ENABLED", True)

    status = autonomy_levels.status()
    assert status["configured_level"] == "A5"
    assert status["a5_enabled"] is True
    assert status["a6_enabled"] is False
    assert status["a7_enabled"] is False
    assert status["a5_execution_authority_expanded"] is False
    assert status["consequential_action_allowed"] is False

    prep = autonomy_levels.evaluate_a5_preparation("PROOF_PACK")
    assert prep["allowed"] is True
    assert prep["preparation_only"] is True
    assert prep["execution_granted"] is False
    assert prep["human_authority_final"] is True

    runtime = autonomy_levels.evaluate_runtime_job("RUNTIME_HEARTBEAT")
    assert runtime["allowed"] is False


def test_a5_rejects_non_preparation_action(monkeypatch):
    monkeypatch.setenv("OAP_AUTONOMY_LEVEL", "A5")
    monkeypatch.setattr(autonomy_levels, "A5_ENABLED", True)

    decision = autonomy_levels.evaluate_a5_preparation("DEPLOY_PRODUCTION")
    assert decision["allowed"] is False
    assert decision["reason"] == "action_not_a5_preparation_allowlist"
    assert decision["execution_granted"] is False
