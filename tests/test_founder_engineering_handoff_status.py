from mission_control import founder_kernel_execution as bridge


def test_configuration_does_not_prove_native_execution(monkeypatch):
    monkeypatch.setenv("OAP_GITHUB_TOKEN", "fixture")
    monkeypatch.setenv("OAP_APPROVAL_SIGNING_KEY", "x" * 32)
    monkeypatch.delenv("OAP_SOVEREIGN_HALT", raising=False)
    monkeypatch.delenv("OAP_MASTER_SOVEREIGN_MODE", raising=False)
    result = bridge.status(branch="oap-mind/existing")
    assert result["configuration_ready"] is True
    assert result["branch_scope_allowed"] is True
    assert result["native_worker_dispatch_connected"] is False
    assert result["native_engineering_execution_verified"] is False
    assert result["execution_granted"] is False
    assert result["live_github_write_verified"] is False
    assert bridge.status()["branch_scope_allowed"] is None


def test_existing_native_branch_remains_outside_builder_scope(monkeypatch):
    monkeypatch.setenv("OAP_GITHUB_TOKEN", "fixture")
    monkeypatch.setenv("OAP_APPROVAL_SIGNING_KEY", "x" * 32)
    monkeypatch.delenv("OAP_SOVEREIGN_HALT", raising=False)
    monkeypatch.delenv("OAP_MASTER_SOVEREIGN_MODE", raising=False)
    result = bridge.status(branch="smi/native-continuous-checkpoint-20261125")
    assert result["branch_scope_allowed"] is False
    assert result["ready"] is False
    assert "branch_outside_existing_builder_scope" in result["blockers"]


def test_short_key_and_emergency_halt_fail_closed(monkeypatch):
    monkeypatch.setenv("OAP_GITHUB_TOKEN", "fixture")
    monkeypatch.setenv("OAP_APPROVAL_SIGNING_KEY", "short")
    monkeypatch.setenv("OAP_SOVEREIGN_HALT", "1")
    result = bridge.status()
    assert result["ready"] is False
    assert result["signing_key_configured"] is False
    assert "emergency_halt_active" in result["blockers"]
