from mission_control import (
    oap_banking_intelligence,
    sika_provider_adapter,
    sika_treasury_controls,
)


def _provider():
    return sika_provider_adapter.build_evidence(
        provider_id="provider-a",
        authority_reference="authority-ref",
        legal_entity_reference="entity-ref",
        environment="production",
        settlement_receipt_contract="receipt-v1",
        refund_contract="refund-v1",
    )


def _bind(monkeypatch, *, regulator, production, scope):
    monkeypatch.setattr(
        oap_banking_intelligence.bank_authorisation_store,
        "readiness_status",
        lambda: {"authorised_bank": regulator},
    )
    monkeypatch.setattr(
        oap_banking_intelligence.sika_production_evidence_store,
        "readiness_status",
        lambda: {"production_gate_passed": production},
    )
    monkeypatch.setattr(
        oap_banking_intelligence.bank_permission_scope,
        "capability_allowed",
        lambda capability: bool(scope),
    )


def test_world_state_fails_closed_without_governed_proof(monkeypatch):
    _bind(monkeypatch, regulator=False, production=False, scope=False)
    state = oap_banking_intelligence.observe(
        treasury=sika_treasury_controls.snapshot(available_sika="1000"),
        provider_evidence=_provider(),
    )
    assert state.may_enter_human_review is False
    assert state.money_moved is False


def test_world_state_can_enter_human_review_without_execution(monkeypatch):
    _bind(monkeypatch, regulator=True, production=True, scope=True)
    state = oap_banking_intelligence.observe(
        treasury=sika_treasury_controls.snapshot(available_sika="1000"),
        provider_evidence=_provider(),
    )
    assert state.may_enter_human_review is True
    assert state.money_moved is False


def test_treasury_shortfall_blocks_human_review(monkeypatch):
    _bind(monkeypatch, regulator=True, production=True, scope=True)
    state = oap_banking_intelligence.observe(
        treasury=sika_treasury_controls.snapshot(
            available_sika="100",
            committed_sika="150",
        ),
        provider_evidence=_provider(),
    )
    assert state.treasury_healthy is False
    assert state.may_enter_human_review is False


def test_capability_world_state_uses_exact_permission_scope(monkeypatch):
    _bind(monkeypatch, regulator=True, production=True, scope=False)
    matrix = oap_banking_intelligence.capability_world_state()
    assert matrix
    assert all(value is False for value in matrix.values())


def test_status_exposes_remaining_real_integration_gaps():
    status = oap_banking_intelligence.status()
    assert status["first_party"] is True
    assert status["duplicate_ledger_created"] is False
    assert status["payment_execution_enabled"] is False
    assert status["money_movement_enabled"] is False
    assert status["blockchain_integrity_integrated"] is False
    assert status["bank_grade_double_entry_integrated"] is True
    assert status["persistent_journal_store_integrated"] is True
    assert status["financial_intelligence_integrated"] is True
    assert status["runtime_reconciliation_integrated"] is False


def test_status_exposes_global_banking_family_and_first_jurisdictions():
    status = oap_banking_intelligence.status()
    assert status["banking_group"] == "OAP Global Banking Group"
    assert status["continental_family"] == [
        "Africa Crown Bank",
        "Europa Crown Bank",
        "Asia Crown Bank",
        "North America Crown Bank",
        "South America Crown Bank",
        "Pacific Crown Bank",
        "Antarctic Reserve",
    ]
    assert status["first_jurisdictions"] == {
        "Africa Crown Bank": "Ghana",
        "Europa Crown Bank": "United Kingdom",
    }
