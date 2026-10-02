from mission_control import (
    sika_execution_gate,
    sika_provider_adapter,
    sika_treasury_controls,
)


def _provider_evidence():
    return sika_provider_adapter.build_evidence(
        provider_id="provider-a",
        authority_reference="authority-ref",
        legal_entity_reference="entity-ref",
        environment="production",
        settlement_receipt_contract="receipt-v1",
        refund_contract="refund-v1",
    )


def _regulator_state(*, authorised):
    return {
        "authorised_bank": authorised,
        "regulated_execution_enabled": authorised,
    }


def test_execution_gate_stays_closed_without_regulator_and_production_proof(
    monkeypatch,
):
    monkeypatch.setattr(
        sika_execution_gate.bank_authorisation_store,
        "readiness_status",
        lambda: _regulator_state(authorised=False),
    )
    treasury = sika_treasury_controls.snapshot(available_sika="1000")
    result = sika_execution_gate.assess(
        treasury=treasury,
        provider_evidence=_provider_evidence(),
        human_authority_approved=True,
    )
    assert result.treasury_healthy is True
    assert result.provider_review_ready is True
    assert result.regulator_authorisation_proven is False
    assert result.execution_authorised is False
    assert result.money_moved is False


def test_execution_gate_requires_human_authority_even_with_all_other_proof(
    monkeypatch,
):
    monkeypatch.setattr(
        sika_execution_gate.bank_authorisation_store,
        "readiness_status",
        lambda: _regulator_state(authorised=True),
    )
    treasury = sika_treasury_controls.snapshot(available_sika="1000")
    result = sika_execution_gate.assess(
        treasury=treasury,
        provider_evidence=_provider_evidence(),
        production_gate_passed=True,
        human_authority_approved=False,
    )
    assert result.regulator_authorisation_proven is True
    assert result.execution_authorised is False


def test_execution_readiness_can_be_true_without_moving_money(monkeypatch):
    monkeypatch.setattr(
        sika_execution_gate.bank_authorisation_store,
        "readiness_status",
        lambda: _regulator_state(authorised=True),
    )
    treasury = sika_treasury_controls.snapshot(available_sika="1000")
    result = sika_execution_gate.assess(
        treasury=treasury,
        provider_evidence=_provider_evidence(),
        production_gate_passed=True,
        human_authority_approved=True,
    )
    assert result.execution_authorised is True
    assert result.money_moved is False


def test_shortfall_blocks_execution_readiness(monkeypatch):
    monkeypatch.setattr(
        sika_execution_gate.bank_authorisation_store,
        "readiness_status",
        lambda: _regulator_state(authorised=True),
    )
    treasury = sika_treasury_controls.snapshot(
        available_sika="100",
        committed_sika="150",
    )
    result = sika_execution_gate.assess(
        treasury=treasury,
        provider_evidence=_provider_evidence(),
        production_gate_passed=True,
        human_authority_approved=True,
    )
    assert result.treasury_healthy is False
    assert result.execution_authorised is False


def test_capability_matrix_is_fail_closed_by_governed_store(monkeypatch):
    monkeypatch.setattr(
        sika_execution_gate.bank_authorisation_store,
        "readiness_status",
        lambda: _regulator_state(authorised=False),
    )
    matrix = sika_execution_gate.capability_matrix(
        production_gate_passed=True,
    )
    assert matrix
    assert all(value is False for value in matrix.values())


def test_status_has_no_regulator_override_or_execution_bypass():
    status = sika_execution_gate.status()
    assert status["caller_regulator_override_allowed"] is False
    assert status["payment_execution_enabled"] is False
    assert status["money_movement_enabled"] is False
    assert status["bypass_path_available"] is False
