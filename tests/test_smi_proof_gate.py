from __future__ import annotations

import json
import logging

import app as app_module
from mission_control import coherent_automation, smi_proof_gate, telemetry


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


def _proven_counts():
    return {
        "store_reachable": True,
        "five_section_reviews": 5,
        "signed_approved_receipts": 1,
        "durable_hrm_receipts": 1,
        "durable_hrm_receipt_store_present": True,
        "founder_smi_reviews": 1,
        "oap_event_receipts": 1,
        "rollback_recovery_receipts": 1,
        "error": None,
    }


def test_green_gate_can_turn_green_without_unlocking_higher_autonomy(monkeypatch):
    monkeypatch.setattr(smi_proof_gate, "_production_counts", _proven_counts)
    monkeypatch.setattr(
        coherent_automation,
        "status",
        lambda: {"ready": True, "signals_valid": True, "signal_count": 21},
    )
    monkeypatch.setattr(
        telemetry,
        "status",
        lambda: {"observability_ready": True},
    )

    snapshot = smi_proof_gate.status()

    assert snapshot["green"] is True
    assert snapshot["missing"] == ()
    assert snapshot["checks"]["signal_contract"] is True
    assert snapshot["checks"]["durable_hrm_receipt"] is True
    assert snapshot["execution_granted"] is False
    assert snapshot["a5_unlocked"] is False
    assert snapshot["a6_unlocked"] is False
    assert snapshot["a7_unlocked"] is False
    assert snapshot["human_authority_final"] is True


def test_signal_contract_failure_keeps_green_gate_closed(monkeypatch):
    monkeypatch.setattr(smi_proof_gate, "_production_counts", _proven_counts)
    monkeypatch.setattr(
        coherent_automation,
        "status",
        lambda: {"ready": False, "signals_valid": False, "signal_count": 20},
    )
    monkeypatch.setattr(
        telemetry,
        "status",
        lambda: {"observability_ready": True},
    )

    snapshot = smi_proof_gate.status()

    assert snapshot["green"] is False
    assert snapshot["checks"]["signal_contract"] is False
    assert "signal_contract" in snapshot["missing"]


def test_local_traffic_alone_cannot_become_production_proof(monkeypatch):
    monkeypatch.setattr(
        smi_proof_gate,
        "_production_counts",
        lambda: {
            "store_reachable": False,
            "five_section_reviews": 5,
            "signed_approved_receipts": 1,
            "durable_hrm_receipts": 0,
            "durable_hrm_receipt_store_present": False,
            "founder_smi_reviews": 1,
            "oap_event_receipts": 1,
            "rollback_recovery_receipts": 1,
            "error": "production_store_not_configured",
        },
    )
    monkeypatch.setattr(
        coherent_automation,
        "status",
        lambda: {"ready": True, "signals_valid": True, "signal_count": 21},
    )
    monkeypatch.setattr(
        telemetry,
        "status",
        lambda: {"observability_ready": True},
    )

    snapshot = smi_proof_gate.status()

    assert snapshot["green"] is False
    assert snapshot["checks"]["observability"] is False
    assert snapshot["checks"]["signal_contract"] is True
    assert snapshot["checks"]["durable_hrm_receipt"] is False
    assert "observability" in snapshot["missing"]
    assert "durable_hrm_receipt" in snapshot["missing"]


def test_smi_proof_snapshot_is_one_shot_allowlisted_and_read_only(monkeypatch, caplog):
    calls = {"status": 0}

    def fake_status():
        calls["status"] += 1
        return {
            "green": True,
            "checks": {
                "rollback_recovery": True,
                "runtime_guard": True,
                "isolation_recovery": True,
            },
            "production_counts": {
                "store_reachable": True,
                "rollback_recovery_receipts": 2,
                "runtime_guard_receipts": 3,
                "isolation_recovery_receipts": 4,
                "receipt_body": "SECRET_RECEIPT_BODY",
            },
            "identity_id": "SECRET_IDENTITY",
            "correlation_id": "SECRET_CORRELATION",
            "signature": "SECRET_SIGNATURE",
            "nonce": "SECRET_NONCE",
            "execution_granted": True,
        }

    def forbidden_write(*args, **kwargs):
        raise AssertionError("snapshot logging must not execute proof/write paths")

    monkeypatch.setattr(app_module, "_SMI_PROOF_SNAPSHOT_LOGGED", False)
    monkeypatch.setattr(app_module, "_current_revision", lambda: "test-revision")
    monkeypatch.setattr(smi_proof_gate, "status", fake_status)
    monkeypatch.setattr(smi_proof_gate, "run_rollback_recovery_proof", forbidden_write)
    monkeypatch.setattr(smi_proof_gate, "run_runtime_guard_proof", forbidden_write)
    monkeypatch.setattr(smi_proof_gate, "run_isolation_recovery_proof", forbidden_write)

    caplog.set_level(logging.INFO, logger=app_module.REQUEST_LOGGER.name)
    app_module._log_smi_proof_snapshot_once()
    app_module._log_smi_proof_snapshot_once()

    snapshot_messages = [
        record.getMessage()
        for record in caplog.records
        if '"event":"oap_smi_proof_snapshot"' in record.getMessage()
    ]
    assert len(snapshot_messages) == 1
    assert calls["status"] == 1

    payload = json.loads(snapshot_messages[0])
    assert payload == {
        "event": "oap_smi_proof_snapshot",
        "revision": "test-revision",
        "rollback_recovery": True,
        "runtime_guard": True,
        "isolation_recovery": True,
        "rollback_recovery_receipts": 2,
        "runtime_guard_receipts": 3,
        "isolation_recovery_receipts": 4,
        "store_reachable": True,
        "green_gate": True,
        "production_state_mutated": False,
        "execution_authority_expanded": False,
        "human_authority_final": True,
    }

    serialized = snapshot_messages[0]
    for forbidden in (
        "SECRET_IDENTITY",
        "SECRET_CORRELATION",
        "SECRET_SIGNATURE",
        "SECRET_NONCE",
        "SECRET_RECEIPT_BODY",
        "identity_id",
        "correlation_id",
        "signature",
        "nonce",
        "receipt_body",
        "execution_granted",
    ):
        assert forbidden not in serialized
