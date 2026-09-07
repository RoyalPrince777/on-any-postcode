from __future__ import annotations

from mission_control import smi_proof_gate, telemetry


def test_first_party_observability_works_without_datadog(monkeypatch):
    monkeypatch.delenv("OAP_DATADOG_ENABLED", raising=False)
    monkeypatch.delenv("DD_API_KEY", raising=False)
    monkeypatch.setattr(telemetry, "_REQUEST_COUNT", 0)
    monkeypatch.setattr(telemetry, "_ERROR_COUNT", 0)
    monkeypatch.setattr(telemetry, "_HEALTH_SUCCESS_COUNT", 0)
    monkeypatch.setattr(telemetry, "_LAST_REQUEST_EPOCH", None)
    monkeypatch.setattr(telemetry, "_LAST_HEALTH_SUCCESS_EPOCH", None)
    monkeypatch.setattr(telemetry, "_LAST_DURATION_MS", None)
    monkeypatch.setattr(telemetry, "_MAX_DURATION_MS", 0.0)

    telemetry.record_http_request(path="/healthz", status_code=200, duration_ms=12.5)
    snapshot = telemetry.status()

    assert snapshot["configured"] is False
    assert snapshot["local_request_count"] == 1
    assert snapshot["local_health_success_count"] == 1
    assert snapshot["local_observability_ready"] is True
    assert snapshot["observability_ready"] is True


def test_bounded_rollback_exercise_restores_and_resumes_without_product_mutation():
    proof = smi_proof_gate._rollback_exercise()

    assert proof["fault_observed"] is True
    assert proof["restored"] is True
    assert proof["safe_resume"] is True
    assert proof["passed"] is True
    assert proof["production_state_mutated"] is False
    assert proof["execution_authority_expanded"] is False
    assert proof["human_authority_final"] is True


def test_green_gate_can_turn_green_without_unlocking_higher_autonomy(monkeypatch):
    monkeypatch.setattr(
        smi_proof_gate,
        "_production_counts",
        lambda: {
            "store_reachable": True,
            "five_section_reviews": 5,
            "signed_approved_receipts": 1,
            "founder_smi_reviews": 1,
            "oap_event_receipts": 1,
            "rollback_recovery_receipts": 1,
            "error": None,
        },
    )
    monkeypatch.setattr(
        telemetry,
        "status",
        lambda: {"observability_ready": True},
    )

    snapshot = smi_proof_gate.status()

    assert snapshot["green"] is True
    assert snapshot["missing"] == ()
    assert snapshot["execution_granted"] is False
    assert snapshot["a5_unlocked"] is False
    assert snapshot["a6_unlocked"] is False
    assert snapshot["a7_unlocked"] is False
    assert snapshot["human_authority_final"] is True


def test_local_traffic_alone_cannot_become_production_proof(monkeypatch):
    monkeypatch.setattr(
        smi_proof_gate,
        "_production_counts",
        lambda: {
            "store_reachable": False,
            "five_section_reviews": 5,
            "signed_approved_receipts": 1,
            "founder_smi_reviews": 1,
            "oap_event_receipts": 1,
            "rollback_recovery_receipts": 1,
            "error": "production_store_not_configured",
        },
    )
    monkeypatch.setattr(
        telemetry,
        "status",
        lambda: {"observability_ready": True},
    )

    snapshot = smi_proof_gate.status()

    assert snapshot["green"] is False
    assert snapshot["checks"]["observability"] is False
    assert "observability" in snapshot["missing"]
