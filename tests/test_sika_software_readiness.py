from mission_control import sika_software_readiness


def test_software_readiness_is_separate_from_external_execution():
    result = sika_software_readiness.assess()
    assert result.external_execution_ready is False
    assert result.ready is True
    assert result.percent == 100
    assert result.checks
    assert all(result.checks.values())


def test_status_excludes_external_responsibilities_without_bypassing_gate():
    status = sika_software_readiness.status()
    assert status["scope"] == "software_only"
    assert "licensing_and_regulatory_authorisation" in (
        status["external_responsibilities_excluded_from_score"]
    )
    assert "payment_provider_contracts" in (
        status["external_responsibilities_excluded_from_score"]
    )
    assert status["execution_gate_bypassed"] is False
    assert status["payment_execution_enabled"] is False
    assert status["money_movement_enabled"] is False
    assert status["human_authority_final"] is True


def test_software_ready_requires_every_internal_check(monkeypatch):
    monkeypatch.setattr(
        sika_software_readiness.sika_account_engine,
        "status",
        lambda: {"persistent_account_identity": False},
    )
    result = sika_software_readiness.assess()
    assert result.ready is False
    assert result.percent < 100


def test_treasury_is_part_of_canonical_software_readiness():
    result = sika_software_readiness.assess()
    assert result.checks["treasury_controls"] is True
