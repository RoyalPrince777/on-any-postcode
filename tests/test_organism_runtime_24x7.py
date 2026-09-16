from pathlib import Path

from mission_control import organism_runtime, organism_worker


def test_worker_health_fails_closed_when_database_is_unavailable(monkeypatch):
    job = {
        "job_id": "job-1",
        "kind": "health",
        "payload": {},
    }
    monkeypatch.setattr(organism_worker, "_database_ready", lambda: False)
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


def test_free_mode_does_not_provision_a_paid_background_worker():
    content = Path("render.yaml").read_text()
    assert "type: worker" not in content
    assert "name: oap-organism-runtime" not in content
    assert "name: oap-smi" in content
    assert "plan: free" in content
    assert "startCommand: gunicorn smi_gateway:app" in content
