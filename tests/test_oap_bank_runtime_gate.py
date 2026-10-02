from mission_control import oap_bank_runtime_gate


def test_runtime_surface_is_installable_but_not_fake_operational_bank(monkeypatch):
    monkeypatch.setattr(
        oap_bank_runtime_gate.bank_authorisation_store,
        "readiness_status",
        lambda: {"authorised_bank": False},
    )
    monkeypatch.setattr(
        oap_bank_runtime_gate.sika_production_evidence_store,
        "readiness_status",
        lambda: {"production_gate_passed": False},
    )
    monkeypatch.setattr(
        oap_bank_runtime_gate.bank_permission_scope,
        "capability_allowed",
        lambda capability: False,
    )

    state = oap_bank_runtime_gate.runtime_status()
    assert state["installed_software_surface_ready"] is True
    assert state["regulated_bank_claim_enabled"] is False
    assert state["operational_bank"] is False
    assert state["deposit_taking_enabled"] is False
    assert state["payment_execution_enabled"] is False
    assert state["bank_accounts_enabled"] is False
    assert state["human_authority_final"] is True


def test_regulated_capability_requires_all_three_external_gates(monkeypatch):
    monkeypatch.setattr(
        oap_bank_runtime_gate.bank_authorisation_store,
        "readiness_status",
        lambda: {"authorised_bank": True},
    )
    monkeypatch.setattr(
        oap_bank_runtime_gate.sika_production_evidence_store,
        "readiness_status",
        lambda: {"production_gate_passed": True},
    )
    monkeypatch.setattr(
        oap_bank_runtime_gate.bank_permission_scope,
        "capability_allowed",
        lambda capability: capability == "execute_payments",
    )

    state = oap_bank_runtime_gate.capability_state("execute_payments")
    assert state["enabled"] is True
    assert state["missing"] == ()

    blocked = oap_bank_runtime_gate.capability_state("accept_deposits")
    assert blocked["enabled"] is False
    assert "permission_scope" in blocked["missing"]


def test_public_claims_fail_closed(monkeypatch):
    monkeypatch.setattr(
        oap_bank_runtime_gate.bank_authorisation_store,
        "readiness_status",
        lambda: {"authorised_bank": False},
    )
    monkeypatch.setattr(
        oap_bank_runtime_gate.sika_production_evidence_store,
        "readiness_status",
        lambda: {"production_gate_passed": False},
    )
    monkeypatch.setattr(
        oap_bank_runtime_gate.bank_permission_scope,
        "capability_allowed",
        lambda capability: False,
    )

    claims = oap_bank_runtime_gate.public_claims()
    assert claims["may_claim_bank_software"] is True
    assert claims["may_claim_regulated_bank"] is False
    assert claims["may_claim_deposit_taking"] is False
    assert claims["may_claim_live_payments"] is False
    assert claims["may_claim_customer_bank_accounts"] is False
    assert claims["must_disclose_software_only_when_locked"] is True


def test_unknown_capability_never_enables():
    state = oap_bank_runtime_gate.capability_state("invented")
    assert state["known"] is False
    assert state["enabled"] is False
