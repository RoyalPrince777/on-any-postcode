from mission_control import sika_production_evidence_store


def test_production_readiness_requires_every_evidence_category(monkeypatch):
    register = {
        key: {
            "proven": True,
            "status": "ACCEPTED",
            "evidence_reference": f"proof-{key}",
            "reviewed_by": "Founder",
        }
        for key in sika_production_evidence_store.PRODUCTION_EVIDENCE
    }
    monkeypatch.setattr(
        sika_production_evidence_store,
        "latest_register",
        lambda: register,
    )
    status = sika_production_evidence_store.readiness_status()
    assert status["production_gate_passed"] is True
    assert status["evidence_proven"] == status["evidence_total"]
    assert status["money_movement_enabled"] is False


def test_missing_production_evidence_fails_closed(monkeypatch):
    register = {
        key: {
            "proven": key != "provider_runtime_readback",
            "status": "ACCEPTED" if key != "provider_runtime_readback" else "MISSING",
        }
        for key in sika_production_evidence_store.PRODUCTION_EVIDENCE
    }
    monkeypatch.setattr(
        sika_production_evidence_store,
        "latest_register",
        lambda: register,
    )
    status = sika_production_evidence_store.readiness_status()
    assert status["production_gate_passed"] is False
    assert "provider_runtime_readback" in status["evidence_missing"]


def test_production_evidence_categories_cover_runtime_and_reconciliation():
    categories = set(sika_production_evidence_store.PRODUCTION_EVIDENCE)
    assert "provider_production_environment" in categories
    assert "settlement_receipt_contract" in categories
    assert "webhook_signature_verification" in categories
    assert "idempotency_controls" in categories
    assert "ledger_reconciliation" in categories
    assert "provider_runtime_readback" in categories
