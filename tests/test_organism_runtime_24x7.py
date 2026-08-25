from __future__ import annotations

from pathlib import Path

import pytest

from mission_control import organism_runtime, organism_worker
from mission_control.organism_runtime import RuntimeJob


def test_runtime_job_allowlist_cannot_be_used_as_execution_bypass():
    assert organism_runtime.ALLOWED_JOB_TYPES == {
        "RUNTIME_HEARTBEAT",
        "RUNTIME_HEALTH_PROBE",
    }
    with pytest.raises(PermissionError, match="not allow-listed"):
        organism_runtime._job_type("promote_evolution_candidate")
    with pytest.raises(PermissionError, match="not allow-listed"):
        organism_runtime._job_type("deploy")


def test_retry_backoff_is_exponential_and_bounded():
    assert organism_runtime.retry_delay_seconds(1) == 5
    assert organism_runtime.retry_delay_seconds(2) == 10
    assert organism_runtime.retry_delay_seconds(3) == 20
    assert organism_runtime.retry_delay_seconds(8) == 640
    assert organism_runtime.retry_delay_seconds(20) == 640


def test_payload_digest_is_stable_and_payload_validation_fails_closed():
    left = organism_runtime.payload_digest({"b": 2, "a": 1})
    right = organism_runtime.payload_digest({"a": 1, "b": 2})
    assert left == right
    assert len(left) == 64
    with pytest.raises(ValueError, match="valid JSON"):
        organism_runtime._payload({"bad": float("nan")})
    with pytest.raises(ValueError, match="too large"):
        organism_runtime._payload({"blob": "x" * 17000})


def test_runtime_schema_requires_explicit_human_invocation(monkeypatch):
    monkeypatch.setattr(
        organism_runtime.postgres_db,
        "postgres_status",
        lambda: {"initialized": True},
    )
    with pytest.raises(RuntimeError, match="Explicit human approval"):
        organism_runtime.init_runtime_schema()


def test_runtime_status_fails_closed_when_base_database_is_not_ready(monkeypatch):
    monkeypatch.setattr(
        organism_runtime.postgres_db,
        "postgres_status",
        lambda: {"initialized": False},
    )
    status = organism_runtime.runtime_status()
    assert status["ready"] is False
    assert status["schema_ready"] is False
    assert status["worker_fresh"] is False
    assert status["error"] == "base_postgres_not_ready"
    assert status["consequential_execution"] is False


def test_worker_refuses_to_start_without_verified_runtime_schema(monkeypatch):
    monkeypatch.setattr(
        organism_worker,
        "runtime_status",
        lambda: {"schema_ready": False, "error": "runtime_schema_pending"},
    )
    assert organism_worker.run() == 2


def test_worker_handlers_are_bounded_nonconsequential(monkeypatch):
    job = RuntimeJob(
        job_id="00000000-0000-0000-0000-000000000001",
        job_type="RUNTIME_HEARTBEAT",
        payload={},
        attempts=1,
        max_attempts=5,
        idempotency_key="test",
    )
    heartbeat = organism_worker._heartbeat_job(job)
    assert heartbeat["consequential_action"] is False

    monkeypatch.setattr(
        organism_worker.postgres_db,
        "postgres_status",
        lambda: {"initialized": False},
    )
    health = organism_worker._health_probe(job)
    assert health["consequential_action"] is False
    assert health["database_ready"] is False
    assert health["human_authority_present"] is False


def test_runtime_migration_contains_durable_queue_recovery_and_receipts():
    sql = "\n".join(organism_runtime.RUNTIME_SCHEMA_STATEMENTS)
    assert "oap_runtime_jobs" in sql
    assert "oap_runtime_workers" in sql
    assert "oap_runtime_schedules" in sql
    assert "oap_runtime_dead_letters" in sql
    assert "oap_runtime_receipts" in sql
    assert "DEAD_LETTER" in sql
    assert len(organism_runtime.RUNTIME_MIGRATION_CHECKSUM) == 64


def test_render_blueprint_defines_real_background_worker():
    content = Path("render.yaml").read_text()
    assert "type: worker" in content
    assert "name: oap-organism-runtime" in content
    assert "startCommand: python -m mission_control.organism_worker" in content
    assert "maxShutdownDelaySeconds: 60" in content
    assert "OAP_DB_SECRET_B64" in content
