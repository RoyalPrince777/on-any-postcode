from __future__ import annotations

from contextlib import contextmanager

import pytest

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
    assert proof["human_stop_observed"] is True
    assert proof["human_stop_idempotent"] is True
    assert proof["human_stop_safe_resume"] is True
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



def test_runtime_guard_exercise_includes_embodiment_boundaries():
    proof = smi_proof_gate._runtime_guard_exercise()

    assert proof["passed"] is True
    assert proof["embodiment_no_execute_state"] is True
    assert proof["embodiment_unknown_motor_blocked"] is True
    assert proof["embodiment_privacy_blocked"] is True
    assert proof["embodiment_restart_blocked"] is True
    assert proof["embodiment_truth_preserved"] is True
    assert proof["embodiment_stop_output_cleared"] is True
    assert proof["execution_authority_expanded"] is False


def test_production_counts_require_fresh_embodiment_proof_revision(monkeypatch):
    captured = {}

    class Result:
        def __init__(self, row):
            self.row = row

        def fetchone(self):
            return self.row

    class Connection:
        def execute(self, query, params=None):
            if "SELECT COUNT(*) FROM smi_judgement_reviews" in query:
                captured["query"] = query
                captured["params"] = params
                return Result((5, 1, 1, 1, 1, 1, 1))
            if "to_regclass" in query:
                return Result((None,))
            raise AssertionError("unexpected query")

    @contextmanager
    def fake_connect(*, readonly=False):
        assert readonly is True
        yield Connection()

    monkeypatch.setattr(smi_proof_gate.postgres_db, "configured", lambda: True)
    monkeypatch.setattr(smi_proof_gate.postgres_db, "connect", fake_connect)

    counts = smi_proof_gate._production_counts()

    assert counts["rollback_recovery_receipts"] == 1
    assert counts["runtime_guard_receipts"] == 1
    assert counts["isolation_recovery_receipts"] == 1
    assert captured["params"] == (
        smi_proof_gate.ROLLBACK_PROOF_ACTION,
        smi_proof_gate.EMBODIMENT_PROOF_REVISION,
        smi_proof_gate.RUNTIME_GUARD_PROOF_ACTION,
        smi_proof_gate.EMBODIMENT_PROOF_REVISION,
        smi_proof_gate.ISOLATION_RECOVERY_PROOF_ACTION,
        smi_proof_gate.EMBODIMENT_PROOF_REVISION,
    )
    assert captured["query"].count("metadata->>'proof_revision'=%s") == 3


def test_founder_final_stays_locked_when_green_gate_is_incomplete(monkeypatch):
    monkeypatch.setattr(
        smi_proof_gate,
        "status",
        lambda: {
            "green": False,
            "missing": ("rollback_recovery", "runtime_guard", "isolation_recovery"),
        },
    )

    with pytest.raises(RuntimeError, match="green_gate_incomplete"):
        smi_proof_gate.run_founder_final("00000000-0000-0000-0000-000000000001")
